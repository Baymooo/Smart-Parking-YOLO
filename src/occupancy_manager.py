class OccupancyManager:
    def __init__(self, total_slots:int):
        """
        total_slots → jumlah total slot parkir yang tersedia
        """
        self.total_slots = total_slots
        self.occupied_slots = 0  # awalnya parkiran kosong

    # ------ Basic Function ------

    def vehicle_enter(self, amount:int=1) -> bool:
        """Kendaraan masuk → slot terpakai bertambah"""
        if self.occupied_slots + amount <= self.total_slots:
            self.occupied_slots += amount
            print(f"[ENTER] {amount} kendaraan masuk → {self.free_slots()} slot tersisa")
            return True
        else:
            print("[FULL] Parkir penuh bro 🚫")
            return False

    def vehicle_exit(self, amount:int=1) -> bool:
        """Kendaraan keluar → slot kosong bertambah"""
        if self.occupied_slots - amount >= 0:
            self.occupied_slots -= amount
            print(f"[EXIT] {amount} kendaraan keluar → {self.free_slots()} slot tersisa")
            return True
        else:
            print("[ERROR] Slot sudah kosong, ga bisa dikurangin lagi")
            return False

    # ------ Status & Monitoring ------

    def is_full(self) -> bool:
        return self.occupied_slots >= self.total_slots

    def free_slots(self) -> int:
        return self.total_slots - self.occupied_slots

    def status(self) -> str:
        if self.is_full():
            return f"Status: FULL 🚨 ({self.occupied_slots}/{self.total_slots})"
        else:
            return f"Status: Available ({self.free_slots()} slot tersisa)"
