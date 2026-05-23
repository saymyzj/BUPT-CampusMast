import { ref, onMounted } from "vue";
import { listCampusBuildings } from "@/api/modules/map";

const buildingNames = ref<Record<string, string>>({});
let fetched = false;

export function useBuildingName() {
  async function ensure() {
    if (fetched) return;
    try {
      const data = await listCampusBuildings();
      const map: Record<string, string> = {};
      for (const b of data) map[b.code] = b.name;
      buildingNames.value = map;
    } catch { /* */ }
    fetched = true;
  }

  function name(code: string): string {
    return buildingNames.value[code] || code;
  }

  return { buildingNames, name, ensure };
}
