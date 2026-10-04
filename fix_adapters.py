import pathlib, re

for f in pathlib.Path("adapters").glob("*.py"):
    if f.name in ("__init__.py", "base_adapter.py"):
        continue
    s = f.read_text(encoding="utf-8")
    if "async def refund" in s:
        continue
    prefix = re.search(r'rail_reference=f"(\w+)-', s).group(1)
    s = s.replace(
        "    async def credit(self, party: Party, amount: Money) -> AdapterResult:\n        await asyncio.sleep(0)\n",
        "    async def credit(self, party: Party, amount: Money) -> AdapterResult:\n        await asyncio.sleep(0)\n"
        "        if self.should_fail_credit():\n"
        "            return AdapterResult(success=False, error=\"injected credit failure\")\n",
    )
    s = s.rstrip() + (
        "\n\n    async def refund(self, party: Party, amount: Money) -> AdapterResult:\n"
        "        await asyncio.sleep(0)\n"
        f"        return AdapterResult(success=True, rail_reference=f\"{prefix}-refund-{{uuid4().hex[:10]}}\")\n"
    )
    f.write_text(s, encoding="utf-8")
    print("patched", f)