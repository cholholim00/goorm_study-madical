-- CreateTable
CREATE TABLE "HealthRecord" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "userId" INTEGER NOT NULL,
    "datetime" DATETIME NOT NULL,
    "type" TEXT NOT NULL,
    "value1" INTEGER NOT NULL,
    "value2" INTEGER,
    "pulse" INTEGER,
    "state" TEXT,
    "sleepHours" INTEGER,
    "exercise" BOOLEAN,
    "stressLevel" INTEGER,
    "memo" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
