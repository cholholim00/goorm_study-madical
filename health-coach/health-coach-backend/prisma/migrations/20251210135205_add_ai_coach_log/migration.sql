-- CreateTable
CREATE TABLE "UserProfile" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "userId" INTEGER NOT NULL,
    "targetSys" INTEGER NOT NULL,
    "targetDia" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "AiCoachLog" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "userId" INTEGER NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "type" TEXT NOT NULL,
    "rangeDays" INTEGER NOT NULL,
    "userNote" TEXT,
    "source" TEXT,
    "aiMessage" TEXT NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "UserProfile_userId_key" ON "UserProfile"("userId");
