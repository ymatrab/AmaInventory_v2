import { PrismaClient } from "@prisma/client";

// Seeds a demo OPEN campaign so the field app + routes can be exercised locally.
// NO system stock / values here (CLAUDE.md §2). PIN hashing arrives in Phase 5.
const prisma = new PrismaClient();

const CAMPAIGN_ID = "demo-campaign";
const WAREHOUSE_ID = "wh-demo-casa";
const AGENT_ID = "AG-1001";

const ITEMS = [
  {
    itemCode: "ITM-001",
    sku: "ITM-001-RED",
    description: "Shampoo 500ml",
    colorParfum: "Red",
    unitsPerPack: 12,
  },
  {
    itemCode: "ITM-001",
    sku: "ITM-001-BLUE",
    description: "Shampoo 500ml",
    colorParfum: "Blue",
    unitsPerPack: 12,
  },
  {
    itemCode: "ITM-002",
    sku: "ITM-002-VANILLA",
    description: "Soap bar",
    colorParfum: "Vanilla",
    unitsPerPack: 24,
  },
];

async function main() {
  const now = Date.now();
  const openAt = new Date(now - 60 * 60 * 1000); // 1h ago
  const closeAt = new Date(now + 7 * 24 * 60 * 60 * 1000); // +7 days

  await prisma.campaign.upsert({
    where: { id: CAMPAIGN_ID },
    update: { status: "OPEN", openAt, closeAt },
    create: { id: CAMPAIGN_ID, code: "DEMO-2026-06", status: "OPEN", openAt, closeAt },
  });

  await prisma.warehouse.upsert({
    where: { id: WAREHOUSE_ID },
    update: {},
    create: {
      id: WAREHOUSE_ID,
      whsCode: "WH-CASA",
      name: "Casablanca Depot",
      city: "Casablanca",
      campaignId: CAMPAIGN_ID,
    },
  });

  for (const it of ITEMS) {
    await prisma.itemRef.upsert({
      where: {
        campaignId_itemCode_sku: { campaignId: CAMPAIGN_ID, itemCode: it.itemCode, sku: it.sku },
      },
      update: {},
      create: { ...it, campaignId: CAMPAIGN_ID },
    });
  }

  await prisma.agent.upsert({
    where: { id: AGENT_ID },
    update: {},
    create: { id: AGENT_ID, fullName: "Agent Demo", role: "AGENT" },
  });

  await prisma.agentCredential.upsert({
    where: { agentId_campaignId: { agentId: AGENT_ID, campaignId: CAMPAIGN_ID } },
    update: { active: true },
    create: {
      agentId: AGENT_ID,
      campaignId: CAMPAIGN_ID,
      token: "demo-token",
      pinHash: "phase5-placeholder",
    },
  });

  // eslint-disable-next-line no-console
  console.log(
    `Seeded OPEN campaign=${CAMPAIGN_ID} warehouse=${WAREHOUSE_ID} agent=${AGENT_ID}\n` +
      `Dev session cookie: ama_session={"agentId":"${AGENT_ID}","campaignId":"${CAMPAIGN_ID}"}`,
  );
}

main()
  .catch((e) => {
    // eslint-disable-next-line no-console
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
