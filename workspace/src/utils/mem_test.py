import os
import psutil
import torch
# import tracemalloc

from src.config import mem_log

# if not tracemalloc.is_tracing():
#     tracemalloc.start(25)


class MemoryCheck:
    @staticmethod
    def torch_snapshot(label: str):
        if torch.cuda.is_available():
            mem_log.info(f"{label}: cuda_stream = {torch.cuda.current_stream()}")

    @staticmethod
    def snapshot(label: str) -> None:
        """
        Снимает snapshot памяти процесса.

        RSS показывает реальное потребление RAM процессом.
        tracemalloc показывает только Python-managed allocations.
        PyTorch показывает свои CPU/CUDA allocations.
        """

        try:
            # with open("/proc/self/status", "r", encoding="utf-8") as f:
            #     status = f.read()
            #
            # rss_kb = 0
            # for line in status.splitlines():
            #     if line.startswith("VmRSS:"):
            #         rss_kb = int(line.split()[1])
            #         break

            process = psutil.Process(os.getpid())

            mem = process.memory_info()
            full = process.memory_full_info()

            # rss_mb = rss_kb / 1024
            rss_mb = mem.rss / 1024 / 1024
            uss_mb = full.uss / 1024 / 1024
            pss_mb = getattr(full, "pss", 0) / 1024 / 1024

        except Exception as ex:
            mem_log.error(f"{type(ex)}\t{ex}")
            rss_mb = -1
            uss_mb = -1
            pss_mb = -1

        python_mb = -1.0
        python_peak_mb = -1.0

        try:
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                python_mb = current / 1024 / 1024
                python_peak_mb = peak / 1024 / 1024
        except:
            python_mb = -1
            python_peak_mb = -1

        # cpu_alloc_mb = -1.0
        cpu_reserved_mb = -1.0
        gpu_alloc_mb = -1.0
        gpu_reserved_mb = -1.0

        # try:
        #     cpu_alloc_mb = torch.memory_allocated("cpu") / 1024 / 1024
        # except Exception as ex:
        #     mem_log.error(f"{type(ex)}\t{ex}")

        if torch.cuda.is_available():
            try:
                gpu_alloc_mb = torch.cuda.memory_allocated() / 1024 / 1024
                gpu_reserved_mb = torch.cuda.memory_reserved() / 1024 / 1024
            except Exception as ex:
                mem_log.error(f"{type(ex)}\t{ex}")

        mem_log.warning(
            f"[MEMORY] {label} | "
            f"rss={rss_mb:.1f} MB | "
            # f"rss2={rss_mb2:.1f} MB | "
            f"uss={uss_mb:.1f} MB | "
            f"pss={pss_mb:.1f} MB | "
            f"python={python_mb:.1f} MB | "
            f"python_peak={python_peak_mb:.1f} MB | "
            # f"torch_cpu={cpu_alloc_mb:.1f} MB | "
            f"cuda_alloc={gpu_alloc_mb:.1f} MB | "
            f"cuda_reserved={gpu_reserved_mb:.1f} MB"
        )
