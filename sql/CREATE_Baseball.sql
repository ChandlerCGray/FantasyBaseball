USE [master]
GO
/****** Object:  Database [Baseball]    Script Date: 3/16/2025 4:23:17 PM ******/
CREATE DATABASE [Baseball]
 CONTAINMENT = NONE
 ON  PRIMARY 
( NAME = N'Baseball', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\DATA\Baseball.mdf' , SIZE = 73728KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON 
( NAME = N'Baseball_log', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\DATA\Baseball_log.ldf' , SIZE = 73728KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
 WITH CATALOG_COLLATION = DATABASE_DEFAULT, LEDGER = OFF
GO
ALTER DATABASE [Baseball] SET COMPATIBILITY_LEVEL = 160
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [Baseball].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [Baseball] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [Baseball] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [Baseball] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [Baseball] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [Baseball] SET ARITHABORT OFF 
GO
ALTER DATABASE [Baseball] SET AUTO_CLOSE OFF 
GO
ALTER DATABASE [Baseball] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [Baseball] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [Baseball] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [Baseball] SET CURSOR_DEFAULT  GLOBAL 
GO
ALTER DATABASE [Baseball] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [Baseball] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [Baseball] SET QUOTED_IDENTIFIER OFF 
GO
ALTER DATABASE [Baseball] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [Baseball] SET  DISABLE_BROKER 
GO
ALTER DATABASE [Baseball] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
GO
ALTER DATABASE [Baseball] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [Baseball] SET TRUSTWORTHY OFF 
GO
ALTER DATABASE [Baseball] SET ALLOW_SNAPSHOT_ISOLATION OFF 
GO
ALTER DATABASE [Baseball] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [Baseball] SET READ_COMMITTED_SNAPSHOT OFF 
GO
ALTER DATABASE [Baseball] SET HONOR_BROKER_PRIORITY OFF 
GO
ALTER DATABASE [Baseball] SET RECOVERY FULL 
GO
ALTER DATABASE [Baseball] SET  MULTI_USER 
GO
ALTER DATABASE [Baseball] SET PAGE_VERIFY CHECKSUM  
GO
ALTER DATABASE [Baseball] SET DB_CHAINING OFF 
GO
ALTER DATABASE [Baseball] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF ) 
GO
ALTER DATABASE [Baseball] SET TARGET_RECOVERY_TIME = 60 SECONDS 
GO
ALTER DATABASE [Baseball] SET DELAYED_DURABILITY = DISABLED 
GO
ALTER DATABASE [Baseball] SET ACCELERATED_DATABASE_RECOVERY = OFF  
GO
EXEC sys.sp_db_vardecimal_storage_format N'Baseball', N'ON'
GO
ALTER DATABASE [Baseball] SET QUERY_STORE = ON
GO
ALTER DATABASE [Baseball] SET QUERY_STORE (OPERATION_MODE = READ_WRITE, CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30), DATA_FLUSH_INTERVAL_SECONDS = 900, INTERVAL_LENGTH_MINUTES = 60, MAX_STORAGE_SIZE_MB = 1000, QUERY_CAPTURE_MODE = AUTO, SIZE_BASED_CLEANUP_MODE = AUTO, MAX_PLANS_PER_QUERY = 200, WAIT_STATS_CAPTURE_MODE = ON)
GO
USE [Baseball]
GO
/****** Object:  User [FangraphsApp]    Script Date: 3/16/2025 4:23:17 PM ******/
CREATE USER [FangraphsApp] FOR LOGIN [FangraphsApp] WITH DEFAULT_SCHEMA=[dbo]
GO
ALTER ROLE [db_datareader] ADD MEMBER [FangraphsApp]
GO
ALTER ROLE [db_datawriter] ADD MEMBER [FangraphsApp]
GO
/****** Object:  Table [dbo].[DimPlayer]    Script Date: 3/16/2025 4:23:17 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DimPlayer](
	[PlayerID] [int] IDENTITY(1,1) NOT NULL,
	[FangraphsPlayerID] [int] NOT NULL,
	[PlayerName] [nvarchar](100) NOT NULL,
	[Bats] [char](1) NULL,
PRIMARY KEY CLUSTERED 
(
	[PlayerID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[DimSeason]    Script Date: 3/16/2025 4:23:17 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DimSeason](
	[SeasonID] [int] IDENTITY(1,1) NOT NULL,
	[SeasonYear] [int] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[SeasonID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[DimTeam]    Script Date: 3/16/2025 4:23:17 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DimTeam](
	[TeamID] [int] IDENTITY(1,1) NOT NULL,
	[TeamName] [nvarchar](100) NOT NULL,
	[TeamNameAbb] [nvarchar](10) NULL,
PRIMARY KEY CLUSTERED 
(
	[TeamID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[FactSeasonProjections]    Script Date: 3/16/2025 4:23:17 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[FactSeasonProjections](
	[ProjectionID] [int] IDENTITY(1,1) NOT NULL,
	[PlayerID] [int] NOT NULL,
	[TeamID] [int] NOT NULL,
	[SeasonID] [int] NOT NULL,
	[ProjectionCycle] [datetime] NOT NULL,
	[Games] [decimal](10, 3) NULL,
	[AtBats] [decimal](10, 3) NULL,
	[PlateAppearances] [decimal](10, 3) NULL,
	[Hits] [decimal](10, 3) NULL,
	[Singles] [decimal](10, 3) NULL,
	[Doubles] [decimal](10, 3) NULL,
	[Triples] [decimal](10, 3) NULL,
	[HomeRuns] [decimal](10, 3) NULL,
	[Runs] [decimal](10, 3) NULL,
	[RBI] [decimal](10, 3) NULL,
	[BaseOnBalls] [decimal](10, 3) NULL,
	[IntentionalWalks] [decimal](10, 3) NULL,
	[StrikeOuts] [decimal](10, 3) NULL,
	[HitByPitch] [decimal](10, 3) NULL,
	[SacrificeFlies] [decimal](10, 3) NULL,
	[SacrificeHits] [decimal](10, 3) NULL,
	[GroundedIntoDoublePlay] [decimal](10, 3) NULL,
	[StolenBases] [decimal](10, 3) NULL,
	[CaughtStealing] [decimal](10, 3) NULL,
	[BattingAverage] [decimal](10, 6) NULL,
	[OnBasePercentage] [decimal](10, 6) NULL,
	[SluggingPercentage] [decimal](10, 6) NULL,
	[OPS] [decimal](10, 6) NULL,
	[wOBA] [decimal](10, 6) NULL,
	[BBPercent] [decimal](10, 6) NULL,
	[KPercent] [decimal](10, 6) NULL,
	[BBPerK] [decimal](10, 6) NULL,
	[ISO] [decimal](10, 6) NULL,
	[Spd] [decimal](10, 6) NULL,
	[BABIP] [decimal](10, 6) NULL,
	[UBR] [decimal](10, 6) NULL,
	[GDPRuns] [decimal](10, 6) NULL,
	[wRC] [decimal](10, 6) NULL,
	[wRAA] [decimal](10, 6) NULL,
	[UZR] [decimal](10, 6) NULL,
	[wBsR] [decimal](10, 6) NULL,
	[BaseRunning] [decimal](10, 6) NULL,
	[WAR] [decimal](10, 6) NULL,
	[Off] [decimal](10, 6) NULL,
	[Def] [decimal](10, 6) NULL,
	[wRCPlus] [decimal](10, 6) NULL,
	[FPTS] [decimal](10, 3) NULL,
	[FPTS_G] [decimal](10, 6) NULL,
	[SPTS] [decimal](10, 3) NULL,
	[SPTS_G] [decimal](10, 6) NULL,
	[woba_sd] [decimal](10, 6) NULL,
	[truetalent_sd] [decimal](10, 6) NULL,
	[woba_sd_book] [decimal](10, 6) NULL,
	[woba_se] [decimal](10, 6) NULL,
	[total_se] [decimal](10, 6) NULL,
	[q10] [decimal](10, 6) NULL,
	[q20] [decimal](10, 6) NULL,
	[q30] [decimal](10, 6) NULL,
	[q40] [decimal](10, 6) NULL,
	[q50] [decimal](10, 6) NULL,
	[q60] [decimal](10, 6) NULL,
	[q70] [decimal](10, 6) NULL,
	[q80] [decimal](10, 6) NULL,
	[q90] [decimal](10, 6) NULL,
	[tt_q10] [decimal](10, 6) NULL,
	[tt_q20] [decimal](10, 6) NULL,
	[tt_q30] [decimal](10, 6) NULL,
	[tt_q40] [decimal](10, 6) NULL,
	[tt_q50] [decimal](10, 6) NULL,
	[tt_q60] [decimal](10, 6) NULL,
	[tt_q70] [decimal](10, 6) NULL,
	[tt_q80] [decimal](10, 6) NULL,
	[tt_q90] [decimal](10, 6) NULL,
	[ADP] [decimal](10, 6) NULL,
	[Pos] [decimal](10, 6) NULL,
	[minpos] [nvarchar](20) NULL,
	[UPURL] [nvarchar](200) NULL,
	[SourceTeam] [nvarchar](50) NULL,
	[SourceShortName] [nvarchar](50) NULL,
	[League] [nvarchar](10) NULL,
	[SourcePlayerName] [nvarchar](100) NULL,
	[Source_xMLBAMID] [int] NULL,
	[SourcePlayerIDs] [nvarchar](50) NULL,
	[SourcePlayerID] [nvarchar](50) NULL,
PRIMARY KEY CLUSTERED 
(
	[ProjectionID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[FactSeasonStatsBatting]    Script Date: 3/16/2025 4:23:17 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[FactSeasonStatsBatting](
	[FactSeasonStatsID] [int] IDENTITY(1,1) NOT NULL,
	[PlayerID] [int] NOT NULL,
	[TeamID] [int] NOT NULL,
	[SeasonID] [int] NOT NULL,
	[Age] [decimal](4, 1) NULL,
	[AgeRange] [nvarchar](20) NULL,
	[SeasonMin] [int] NULL,
	[SeasonMax] [int] NULL,
	[Games] [decimal](5, 1) NULL,
	[AtBats] [decimal](10, 1) NULL,
	[PlateAppearances] [decimal](10, 1) NULL,
	[Hits] [decimal](10, 1) NULL,
	[Singles] [decimal](10, 1) NULL,
	[Doubles] [decimal](10, 1) NULL,
	[Triples] [decimal](10, 1) NULL,
	[HomeRuns] [decimal](10, 1) NULL,
	[Runs] [decimal](10, 1) NULL,
	[RBI] [decimal](10, 1) NULL,
	[BaseOnBalls] [decimal](10, 1) NULL,
	[IntentionalWalks] [decimal](10, 1) NULL,
	[StrikeOuts] [decimal](10, 1) NULL,
	[HitByPitch] [decimal](10, 1) NULL,
	[SacrificeFlies] [decimal](10, 1) NULL,
	[SacrificeHits] [decimal](10, 1) NULL,
	[GroundedIntoDoublePlay] [decimal](10, 1) NULL,
	[StolenBases] [decimal](10, 1) NULL,
	[CaughtStealing] [decimal](10, 1) NULL,
	[BattingAverage] [decimal](10, 4) NULL,
	[GroundBalls] [decimal](10, 1) NULL,
	[FlyBalls] [decimal](10, 1) NULL,
	[LineDrives] [decimal](10, 1) NULL,
	[InfieldFlyBalls] [decimal](10, 1) NULL,
	[Pitches] [decimal](10, 1) NULL,
	[Balls] [decimal](10, 1) NULL,
	[Strikes] [decimal](10, 1) NULL,
	[IFH] [decimal](10, 1) NULL,
	[BU] [decimal](10, 1) NULL,
	[BUH] [decimal](10, 1) NULL,
	[BBPercent] [decimal](10, 6) NULL,
	[KPercent] [decimal](10, 6) NULL,
	[BBPerK] [decimal](10, 6) NULL,
	[OnBasePercentage] [decimal](10, 4) NULL,
	[SluggingPercentage] [decimal](10, 4) NULL,
	[OPS] [decimal](10, 4) NULL,
	[ISO] [decimal](10, 4) NULL,
	[BABIP] [decimal](10, 4) NULL,
	[GB_FB_Ratio] [decimal](10, 6) NULL,
	[LDPercent] [decimal](10, 6) NULL,
	[GBPercent] [decimal](10, 6) NULL,
	[FBPercent] [decimal](10, 6) NULL,
	[IFFBPercent] [decimal](10, 6) NULL,
	[HR_FB_Ratio] [decimal](10, 6) NULL,
	[IFHPercent] [decimal](10, 6) NULL,
	[BUHPercent] [decimal](10, 6) NULL,
	[TTOPercent] [decimal](10, 6) NULL,
	[wOBA] [decimal](10, 6) NULL,
	[wRAA] [decimal](10, 6) NULL,
	[wRC] [decimal](10, 6) NULL,
	[BattingValue] [decimal](10, 6) NULL,
	[Fielding] [decimal](10, 6) NULL,
	[Replacement] [decimal](10, 6) NULL,
	[Positional] [decimal](10, 6) NULL,
	[wLeague] [decimal](10, 6) NULL,
	[CFraming] [decimal](10, 6) NULL,
	[Defense] [decimal](10, 6) NULL,
	[Offense] [decimal](10, 6) NULL,
	[RAR] [decimal](10, 6) NULL,
	[WAR] [decimal](10, 6) NULL,
	[WAROld] [decimal](10, 6) NULL,
	[Dollars] [decimal](10, 6) NULL,
	[BaseRunning] [decimal](10, 6) NULL,
	[Spd] [decimal](10, 6) NULL,
	[wRCPlus] [decimal](10, 6) NULL,
	[wBsR] [decimal](10, 6) NULL,
	[WPA] [decimal](10, 6) NULL,
	[WPA_Negative] [decimal](10, 6) NULL,
	[WPA_Positive] [decimal](10, 6) NULL,
	[RE24] [decimal](10, 6) NULL,
	[REW] [decimal](10, 6) NULL,
	[pLI] [decimal](10, 6) NULL,
	[phLI] [decimal](10, 6) NULL,
	[PH] [decimal](10, 1) NULL,
	[WPA_per_LI] [decimal](10, 6) NULL,
	[Clutch] [decimal](10, 6) NULL,
	[FBPercent1] [decimal](10, 6) NULL,
	[FBv] [decimal](10, 6) NULL,
	[SLPercent] [decimal](10, 6) NULL,
	[SLv] [decimal](10, 6) NULL,
	[CTPercent] [decimal](10, 6) NULL,
	[CTv] [decimal](10, 6) NULL,
	[CBPercent] [decimal](10, 6) NULL,
	[CBv] [decimal](10, 6) NULL,
	[CHPercent] [decimal](10, 6) NULL,
	[CHv] [decimal](10, 6) NULL,
	[SFPercent] [decimal](10, 6) NULL,
	[SFv] [decimal](10, 6) NULL,
	[KNPercent] [decimal](10, 6) NULL,
	[KNv] [decimal](10, 6) NULL,
	[XXPercent] [decimal](10, 6) NULL,
	[POPercent] [decimal](10, 6) NULL,
	[wFB] [decimal](10, 6) NULL,
	[wSL] [decimal](10, 6) NULL,
	[wCT] [decimal](10, 6) NULL,
	[wCB] [decimal](10, 6) NULL,
	[wCH] [decimal](10, 6) NULL,
	[wSF] [decimal](10, 6) NULL,
	[wKN] [decimal](10, 6) NULL,
	[wFB_PerC] [decimal](10, 6) NULL,
	[wSL_PerC] [decimal](10, 6) NULL,
	[wCT_PerC] [decimal](10, 6) NULL,
	[wCB_PerC] [decimal](10, 6) NULL,
	[wCH_PerC] [decimal](10, 6) NULL,
	[wSF_PerC] [decimal](10, 6) NULL,
	[wKN_PerC] [decimal](10, 6) NULL,
	[OSwingPercent] [decimal](10, 6) NULL,
	[ZSwingPercent] [decimal](10, 6) NULL,
	[SwingPercent] [decimal](10, 6) NULL,
	[OContactPercent] [decimal](10, 6) NULL,
	[ZContactPercent] [decimal](10, 6) NULL,
	[ContactPercent] [decimal](10, 6) NULL,
	[ZonePercent] [decimal](10, 6) NULL,
	[FStrikePercent] [decimal](10, 6) NULL,
	[SwStrPercent] [decimal](10, 6) NULL,
	[CStrPercent] [decimal](10, 6) NULL,
	[CPlusSwStrPercent] [decimal](10, 6) NULL,
	[Pull] [decimal](10, 1) NULL,
	[Cent] [decimal](10, 1) NULL,
	[Oppo] [decimal](10, 1) NULL,
	[Soft] [decimal](10, 1) NULL,
	[Med] [decimal](10, 1) NULL,
	[Hard] [decimal](10, 1) NULL,
	[bipCount] [decimal](10, 1) NULL,
	[PullPercent] [decimal](10, 6) NULL,
	[CentPercent] [decimal](10, 6) NULL,
	[OppoPercent] [decimal](10, 6) NULL,
	[SoftPercent] [decimal](10, 6) NULL,
	[MedPercent] [decimal](10, 6) NULL,
	[HardPercent] [decimal](10, 6) NULL,
	[UBR] [decimal](10, 6) NULL,
	[GDPRuns] [decimal](10, 6) NULL,
	[AVGPlus] [decimal](10, 6) NULL,
	[BBPlus] [decimal](10, 6) NULL,
	[KPlus] [decimal](10, 6) NULL,
	[OBPPlus] [decimal](10, 6) NULL,
	[SLGPlus] [decimal](10, 6) NULL,
	[ISOPlus] [decimal](10, 6) NULL,
	[BABIPPlus] [decimal](10, 6) NULL,
	[LDPlus] [decimal](10, 6) NULL,
	[GBPlus] [decimal](10, 6) NULL,
	[FBPlus] [decimal](10, 6) NULL,
	[HRFBPlus] [decimal](10, 6) NULL,
	[PullPlus] [decimal](10, 6) NULL,
	[CentPlus] [decimal](10, 6) NULL,
	[OppoPlus] [decimal](10, 6) NULL,
	[SoftPlus] [decimal](10, 6) NULL,
	[MedPlus] [decimal](10, 6) NULL,
	[HardPlus] [decimal](10, 6) NULL,
	[xwOBA] [decimal](10, 6) NULL,
	[xAVG] [decimal](10, 6) NULL,
	[xSLG] [decimal](10, 6) NULL,
	[XBR] [decimal](10, 6) NULL,
	[PPTV] [decimal](10, 6) NULL,
	[CPTV] [decimal](10, 6) NULL,
	[BPTV] [decimal](10, 6) NULL,
	[DSV] [decimal](10, 6) NULL,
	[DGV] [decimal](10, 6) NULL,
	[BTV] [decimal](10, 6) NULL,
	[rPPTV] [decimal](10, 6) NULL,
	[rCPTV] [decimal](10, 6) NULL,
	[rBPTV] [decimal](10, 6) NULL,
	[rDSV] [decimal](10, 6) NULL,
	[rDGV] [decimal](10, 6) NULL,
	[rBTV] [decimal](10, 6) NULL,
	[EBV] [decimal](10, 6) NULL,
	[ESV] [decimal](10, 6) NULL,
	[rFTeamV] [decimal](10, 6) NULL,
	[rBTeamV] [decimal](10, 6) NULL,
	[rTV] [decimal](10, 6) NULL,
	[pfxFA_Percent] [decimal](10, 6) NULL,
	[pfxFT_Percent] [decimal](10, 6) NULL,
	[pfxFC_Percent] [decimal](10, 6) NULL,
	[pfxFS_Percent] [decimal](10, 6) NULL,
	[pfxFO_Percent] [decimal](10, 6) NULL,
	[pfxSI_Percent] [decimal](10, 6) NULL,
	[pfxSL_Percent] [decimal](10, 6) NULL,
	[pfxCU_Percent] [decimal](10, 6) NULL,
	[pfxKC_Percent] [decimal](10, 6) NULL,
	[pfxEP_Percent] [decimal](10, 6) NULL,
	[pfxCH_Percent] [decimal](10, 6) NULL,
	[pfxSC_Percent] [decimal](10, 6) NULL,
	[pfxKN_Percent] [decimal](10, 6) NULL,
	[pfxUN_Percent] [decimal](10, 6) NULL,
	[pfxvFA] [decimal](10, 6) NULL,
	[pfxvFT] [decimal](10, 6) NULL,
	[pfxvFC] [decimal](10, 6) NULL,
	[pfxvFS] [decimal](10, 6) NULL,
	[pfxvFO] [decimal](10, 6) NULL,
	[pfxvSI] [decimal](10, 6) NULL,
	[pfxvSL] [decimal](10, 6) NULL,
	[pfxvCU] [decimal](10, 6) NULL,
	[pfxvKC] [decimal](10, 6) NULL,
	[pfxvEP] [decimal](10, 6) NULL,
	[pfxvCH] [decimal](10, 6) NULL,
	[pfxvSC] [decimal](10, 6) NULL,
	[pfxvKN] [decimal](10, 6) NULL,
	[pfxFA_X] [decimal](10, 6) NULL,
	[pfxFT_X] [decimal](10, 6) NULL,
	[pfxFC_X] [decimal](10, 6) NULL,
	[pfxFS_X] [decimal](10, 6) NULL,
	[pfxFO_X] [decimal](10, 6) NULL,
	[pfxSI_X] [decimal](10, 6) NULL,
	[pfxSL_X] [decimal](10, 6) NULL,
	[pfxCU_X] [decimal](10, 6) NULL,
	[pfxKC_X] [decimal](10, 6) NULL,
	[pfxEP_X] [decimal](10, 6) NULL,
	[pfxCH_X] [decimal](10, 6) NULL,
	[pfxSC_X] [decimal](10, 6) NULL,
	[pfxKN_X] [decimal](10, 6) NULL,
	[pfxFA_Z] [decimal](10, 6) NULL,
	[pfxFT_Z] [decimal](10, 6) NULL,
	[pfxFC_Z] [decimal](10, 6) NULL,
	[pfxFS_Z] [decimal](10, 6) NULL,
	[pfxFO_Z] [decimal](10, 6) NULL,
	[pfxSI_Z] [decimal](10, 6) NULL,
	[pfxSL_Z] [decimal](10, 6) NULL,
	[pfxCU_Z] [decimal](10, 6) NULL,
	[pfxKC_Z] [decimal](10, 6) NULL,
	[pfxEP_Z] [decimal](10, 6) NULL,
	[pfxCH_Z] [decimal](10, 6) NULL,
	[pfxSC_Z] [decimal](10, 6) NULL,
	[pfxKN_Z] [decimal](10, 6) NULL,
	[pfxwFA] [decimal](10, 6) NULL,
	[pfxwFT] [decimal](10, 6) NULL,
	[pfxwFC] [decimal](10, 6) NULL,
	[pfxwFS] [decimal](10, 6) NULL,
	[pfxwFO] [decimal](10, 6) NULL,
	[pfxwSI] [decimal](10, 6) NULL,
	[pfxwSL] [decimal](10, 6) NULL,
	[pfxwCU] [decimal](10, 6) NULL,
	[pfxwKC] [decimal](10, 6) NULL,
	[pfxwEP] [decimal](10, 6) NULL,
	[pfxwCH] [decimal](10, 6) NULL,
	[pfxwSC] [decimal](10, 6) NULL,
	[pfxwKN] [decimal](10, 6) NULL,
	[pfxwFA_PerC] [decimal](10, 6) NULL,
	[pfxwFT_PerC] [decimal](10, 6) NULL,
	[pfxwFC_PerC] [decimal](10, 6) NULL,
	[pfxwFS_PerC] [decimal](10, 6) NULL,
	[pfxwFO_PerC] [decimal](10, 6) NULL,
	[pfxwSI_PerC] [decimal](10, 6) NULL,
	[pfxwSL_PerC] [decimal](10, 6) NULL,
	[pfxwCU_PerC] [decimal](10, 6) NULL,
	[pfxwKC_PerC] [decimal](10, 6) NULL,
	[pfxwEP_PerC] [decimal](10, 6) NULL,
	[pfxwCH_PerC] [decimal](10, 6) NULL,
	[pfxwSC_PerC] [decimal](10, 6) NULL,
	[pfxwKN_PerC] [decimal](10, 6) NULL,
	[pfxO_Swing_Percent] [decimal](10, 6) NULL,
	[pfxZ_Swing_Percent] [decimal](10, 6) NULL,
	[pfxSwing_Percent] [decimal](10, 6) NULL,
	[pfxO_Contact_Percent] [decimal](10, 6) NULL,
	[pfxZ_Contact_Percent] [decimal](10, 6) NULL,
	[pfxContact_Percent] [decimal](10, 6) NULL,
	[pfxZone_Percent] [decimal](10, 6) NULL,
	[pfxPace] [decimal](10, 6) NULL,
	[piCH_Percent] [decimal](10, 6) NULL,
	[piCS_Percent] [decimal](10, 6) NULL,
	[piCU_Percent] [decimal](10, 6) NULL,
	[piFA_Percent] [decimal](10, 6) NULL,
	[piFC_Percent] [decimal](10, 6) NULL,
	[piFS_Percent] [decimal](10, 6) NULL,
	[piKN_Percent] [decimal](10, 6) NULL,
	[piSB_Percent] [decimal](10, 6) NULL,
	[piSI_Percent] [decimal](10, 6) NULL,
	[piSL_Percent] [decimal](10, 6) NULL,
	[piXX_Percent] [decimal](10, 6) NULL,
	[pivCH] [decimal](10, 6) NULL,
	[pivCS] [decimal](10, 6) NULL,
	[pivCU] [decimal](10, 6) NULL,
	[pivFA] [decimal](10, 6) NULL,
	[pivFC] [decimal](10, 6) NULL,
	[pivFS] [decimal](10, 6) NULL,
	[pivKN] [decimal](10, 6) NULL,
	[pivSB] [decimal](10, 6) NULL,
	[pivSI] [decimal](10, 6) NULL,
	[pivSL] [decimal](10, 6) NULL,
	[pivXX] [decimal](10, 6) NULL,
	[piCH_X] [decimal](10, 6) NULL,
	[piCS_X] [decimal](10, 6) NULL,
	[piCU_X] [decimal](10, 6) NULL,
	[piFA_X] [decimal](10, 6) NULL,
	[piFC_X] [decimal](10, 6) NULL,
	[piFS_X] [decimal](10, 6) NULL,
	[piKN_X] [decimal](10, 6) NULL,
	[piSB_X] [decimal](10, 6) NULL,
	[piSI_X] [decimal](10, 6) NULL,
	[piSL_X] [decimal](10, 6) NULL,
	[piXX_X] [decimal](10, 6) NULL,
	[piCH_Z] [decimal](10, 6) NULL,
	[piCS_Z] [decimal](10, 6) NULL,
	[piCU_Z] [decimal](10, 6) NULL,
	[piFA_Z] [decimal](10, 6) NULL,
	[piFC_Z] [decimal](10, 6) NULL,
	[piFS_Z] [decimal](10, 6) NULL,
	[piKN_Z] [decimal](10, 6) NULL,
	[piSB_Z] [decimal](10, 6) NULL,
	[piSI_Z] [decimal](10, 6) NULL,
	[piSL_Z] [decimal](10, 6) NULL,
	[piXX_Z] [decimal](10, 6) NULL,
	[piwCH] [decimal](10, 6) NULL,
	[piwCS] [decimal](10, 6) NULL,
	[piwCU] [decimal](10, 6) NULL,
	[piwFA] [decimal](10, 6) NULL,
	[piwFC] [decimal](10, 6) NULL,
	[piwFS] [decimal](10, 6) NULL,
	[piwKN] [decimal](10, 6) NULL,
	[piwSB] [decimal](10, 6) NULL,
	[piwSI] [decimal](10, 6) NULL,
	[piwSL] [decimal](10, 6) NULL,
	[piwXX] [decimal](10, 6) NULL,
	[piwCH_PerC] [decimal](10, 6) NULL,
	[piwCS_PerC] [decimal](10, 6) NULL,
	[piwCU_PerC] [decimal](10, 6) NULL,
	[piwFA_PerC] [decimal](10, 6) NULL,
	[piwFC_PerC] [decimal](10, 6) NULL,
	[piwFS_PerC] [decimal](10, 6) NULL,
	[piwKN_PerC] [decimal](10, 6) NULL,
	[piwSB_PerC] [decimal](10, 6) NULL,
	[piwSI_PerC] [decimal](10, 6) NULL,
	[piwSL_PerC] [decimal](10, 6) NULL,
	[piwXX_PerC] [decimal](10, 6) NULL,
	[piO_Swing_Percent] [decimal](10, 6) NULL,
	[piZ_Swing_Percent] [decimal](10, 6) NULL,
	[piSwing_Percent] [decimal](10, 6) NULL,
	[piO_Contact_Percent] [decimal](10, 6) NULL,
	[piZ_Contact_Percent] [decimal](10, 6) NULL,
	[piContact_Percent] [decimal](10, 6) NULL,
	[piZone_Percent] [decimal](10, 6) NULL,
	[piPace] [decimal](10, 6) NULL,
	[Events] [decimal](10, 1) NULL,
	[EV] [decimal](10, 6) NULL,
	[LA] [decimal](10, 6) NULL,
	[Barrels] [decimal](10, 1) NULL,
	[BarrelPercent] [decimal](10, 6) NULL,
	[maxEV] [decimal](10, 6) NULL,
	[HardHit] [decimal](10, 1) NULL,
	[HardHitPercent] [decimal](10, 6) NULL,
	[Q] [decimal](10, 6) NULL,
	[TG] [decimal](10, 1) NULL,
	[TPA] [decimal](10, 1) NULL,
	[PlayerNameRoute] [nvarchar](100) NULL,
	[PlayerNameDup] [nvarchar](100) NULL,
	[position] [nvarchar](10) NULL,
	[SourcePlayerID] [int] NULL,
	[TeamName] [nvarchar](100) NULL,
	[SourceTeamNameAbb] [nvarchar](10) NULL,
	[SourceTeamID] [int] NULL,
	[Pos] [decimal](10, 6) NULL,
PRIMARY KEY CLUSTERED 
(
	[FactSeasonStatsID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[FactSeasonStatsPitching]    Script Date: 3/16/2025 4:23:17 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[FactSeasonStatsPitching](
	[FactSeasonStatsID] [int] IDENTITY(1,1) NOT NULL,
	[Throws] [nvarchar](1) NULL,
	[xMLBAMID] [int] NULL,
	[Name] [nvarchar](200) NULL,
	[Team] [nvarchar](200) NULL,
	[Season] [int] NULL,
	[Age] [decimal](4, 1) NULL,
	[AgeR] [nvarchar](20) NULL,
	[SeasonMin] [int] NULL,
	[SeasonMax] [int] NULL,
	[W] [decimal](10, 1) NULL,
	[L] [decimal](10, 1) NULL,
	[ERA] [decimal](10, 6) NULL,
	[G] [decimal](10, 1) NULL,
	[GS] [decimal](10, 1) NULL,
	[QS] [decimal](10, 1) NULL,
	[CG] [decimal](10, 1) NULL,
	[ShO] [decimal](10, 1) NULL,
	[SV] [decimal](10, 1) NULL,
	[BS] [decimal](10, 1) NULL,
	[IP] [decimal](10, 1) NULL,
	[TBF] [decimal](10, 1) NULL,
	[H] [decimal](10, 1) NULL,
	[R] [decimal](10, 1) NULL,
	[ER] [decimal](10, 1) NULL,
	[HR] [decimal](10, 1) NULL,
	[BB] [decimal](10, 1) NULL,
	[IBB] [decimal](10, 1) NULL,
	[HBP] [decimal](10, 1) NULL,
	[WP] [decimal](10, 1) NULL,
	[BK] [decimal](10, 1) NULL,
	[SO] [decimal](10, 1) NULL,
	[GB] [decimal](10, 1) NULL,
	[FB] [decimal](10, 1) NULL,
	[LD] [decimal](10, 1) NULL,
	[IFFB] [decimal](10, 1) NULL,
	[Pitches] [decimal](10, 1) NULL,
	[Balls] [decimal](10, 1) NULL,
	[Strikes] [decimal](10, 1) NULL,
	[RS] [decimal](10, 1) NULL,
	[IFH] [decimal](10, 1) NULL,
	[BU] [decimal](10, 1) NULL,
	[BUH] [decimal](10, 1) NULL,
	[KPer9] [decimal](18, 6) NULL,
	[BBPer9] [decimal](18, 6) NULL,
	[K_BB] [decimal](18, 6) NULL,
	[HPer9] [decimal](18, 6) NULL,
	[HRPer9] [decimal](18, 6) NULL,
	[AVG] [decimal](18, 6) NULL,
	[WHIP] [decimal](18, 6) NULL,
	[BABIP] [decimal](18, 6) NULL,
	[LOBPercent] [decimal](18, 6) NULL,
	[FIP] [decimal](18, 6) NULL,
	[GB_FB] [decimal](18, 6) NULL,
	[LDPercent] [decimal](18, 6) NULL,
	[GBPercent] [decimal](18, 6) NULL,
	[FBPercent] [decimal](18, 6) NULL,
	[IFFBPercent] [decimal](18, 6) NULL,
	[HR_FB] [decimal](18, 6) NULL,
	[IFHPercent] [decimal](18, 6) NULL,
	[BUHPercent] [decimal](18, 6) NULL,
	[TTOPercent] [decimal](18, 6) NULL,
	[CFraming] [decimal](18, 6) NULL,
	[Starting] [decimal](18, 6) NULL,
	[Start_IP] [decimal](10, 1) NULL,
	[Relieving] [decimal](18, 6) NULL,
	[Relief_IP] [decimal](10, 1) NULL,
	[RAR] [decimal](18, 6) NULL,
	[WAR] [decimal](18, 6) NULL,
	[Dollars] [decimal](18, 6) NULL,
	[RA9_Wins] [decimal](18, 6) NULL,
	[LOB_Wins] [decimal](18, 6) NULL,
	[BIP_Wins] [decimal](18, 6) NULL,
	[BS_Wins] [decimal](18, 6) NULL,
	[tERA] [decimal](18, 6) NULL,
	[xFIP] [decimal](18, 6) NULL,
	[WPA] [decimal](18, 6) NULL,
	[Negative_WPA] [decimal](18, 6) NULL,
	[Positive_WPA] [decimal](18, 6) NULL,
	[RE24] [decimal](18, 6) NULL,
	[REW] [decimal](18, 6) NULL,
	[pLI] [decimal](18, 6) NULL,
	[inLI] [decimal](18, 6) NULL,
	[gmLI] [decimal](18, 6) NULL,
	[exLI] [decimal](18, 6) NULL,
	[Pulls] [decimal](10, 1) NULL,
	[Games] [decimal](10, 1) NULL,
	[WPA_LI] [decimal](18, 6) NULL,
	[Clutch] [decimal](18, 6) NULL,
	[FBPercent1] [decimal](18, 6) NULL,
	[FBv] [decimal](18, 6) NULL,
	[SLPercent] [decimal](18, 6) NULL,
	[SLv] [decimal](18, 6) NULL,
	[CTPercent] [decimal](18, 6) NULL,
	[CTv] [decimal](18, 6) NULL,
	[CBPercent] [decimal](18, 6) NULL,
	[CBv] [decimal](18, 6) NULL,
	[CHPercent] [decimal](18, 6) NULL,
	[CHv] [decimal](18, 6) NULL,
	[SFPercent] [decimal](18, 6) NULL,
	[SFv] [decimal](18, 6) NULL,
	[KNPercent] [decimal](18, 6) NULL,
	[KNv] [decimal](18, 6) NULL,
	[XXPercent] [decimal](18, 6) NULL,
	[POPercent] [decimal](18, 6) NULL,
	[wFB] [decimal](18, 6) NULL,
	[wSL] [decimal](18, 6) NULL,
	[wCT] [decimal](18, 6) NULL,
	[wCB] [decimal](18, 6) NULL,
	[wCH] [decimal](18, 6) NULL,
	[wSF] [decimal](18, 6) NULL,
	[wKN] [decimal](18, 6) NULL,
	[wFB_PerC] [decimal](18, 6) NULL,
	[wSL_PerC] [decimal](18, 6) NULL,
	[wCT_PerC] [decimal](18, 6) NULL,
	[wCB_PerC] [decimal](18, 6) NULL,
	[wCH_PerC] [decimal](18, 6) NULL,
	[wSF_PerC] [decimal](18, 6) NULL,
	[wKN_PerC] [decimal](18, 6) NULL,
	[O_SwingPercent] [decimal](18, 6) NULL,
	[Z_SwingPercent] [decimal](18, 6) NULL,
	[SwingPercent] [decimal](18, 6) NULL,
	[O_ContactPercent] [decimal](18, 6) NULL,
	[Z_ContactPercent] [decimal](18, 6) NULL,
	[ContactPercent] [decimal](18, 6) NULL,
	[ZonePercent] [decimal](18, 6) NULL,
	[F_StrikePercent] [decimal](18, 6) NULL,
	[SwStrPercent] [decimal](18, 6) NULL,
	[CStrPercent] [decimal](18, 6) NULL,
	[CPlusSwStrPercent] [decimal](18, 6) NULL,
	[HLD] [decimal](10, 1) NULL,
	[SD] [decimal](10, 1) NULL,
	[MD] [decimal](10, 1) NULL,
	[ERA_Minus] [decimal](18, 6) NULL,
	[FIP_Minus] [decimal](18, 6) NULL,
	[xFIP_Minus] [decimal](18, 6) NULL,
	[KPercent] [decimal](18, 6) NULL,
	[BBPercent] [decimal](18, 6) NULL,
	[K_BBPercent] [decimal](18, 6) NULL,
	[SIERA] [decimal](18, 6) NULL,
	[kwERA] [decimal](18, 6) NULL,
	[RS_Per9] [decimal](18, 6) NULL,
	[E_F] [decimal](18, 6) NULL,
	[Pull] [decimal](10, 1) NULL,
	[Cent] [decimal](10, 1) NULL,
	[Oppo] [decimal](10, 1) NULL,
	[Soft] [decimal](10, 1) NULL,
	[Med] [decimal](10, 1) NULL,
	[Hard] [decimal](10, 1) NULL,
	[bipCount] [decimal](10, 1) NULL,
	[PullPercent] [decimal](18, 6) NULL,
	[CentPercent] [decimal](18, 6) NULL,
	[OppoPercent] [decimal](18, 6) NULL,
	[SoftPercent] [decimal](18, 6) NULL,
	[MedPercent] [decimal](18, 6) NULL,
	[HardPercent] [decimal](18, 6) NULL,
	[KPer9_Plus] [decimal](18, 6) NULL,
	[BBPer9_Plus] [decimal](18, 6) NULL,
	[K_BB_Plus] [decimal](18, 6) NULL,
	[HPer9_Plus] [decimal](18, 6) NULL,
	[HRPer9_Plus] [decimal](18, 6) NULL,
	[AVG_Plus] [decimal](18, 6) NULL,
	[WHIP_Plus] [decimal](18, 6) NULL,
	[BABIP_Plus] [decimal](18, 6) NULL,
	[LOBPercent_Plus] [decimal](18, 6) NULL,
	[KPercent_Plus] [decimal](18, 6) NULL,
	[BBPercent_Plus] [decimal](18, 6) NULL,
	[LDPercent_Plus] [decimal](18, 6) NULL,
	[GBPercent_Plus] [decimal](18, 6) NULL,
	[FBPercent_Plus] [decimal](18, 6) NULL,
	[HRFBPercent_Plus] [decimal](18, 6) NULL,
	[PullPercent_Plus] [decimal](18, 6) NULL,
	[CentPercent_Plus] [decimal](18, 6) NULL,
	[OppoPercent_Plus] [decimal](18, 6) NULL,
	[SoftPercent_Plus] [decimal](18, 6) NULL,
	[MedPercent_Plus] [decimal](18, 6) NULL,
	[HardPercent_Plus] [decimal](18, 6) NULL,
	[pb_o_CH] [decimal](18, 6) NULL,
	[pb_s_CH] [decimal](18, 6) NULL,
	[pb_c_CH] [decimal](18, 6) NULL,
	[pb_o_CU] [decimal](18, 6) NULL,
	[pb_s_CU] [decimal](18, 6) NULL,
	[pb_c_CU] [decimal](18, 6) NULL,
	[pb_o_FF] [decimal](18, 6) NULL,
	[pb_s_FF] [decimal](18, 6) NULL,
	[pb_c_FF] [decimal](18, 6) NULL,
	[pb_o_SI] [decimal](18, 6) NULL,
	[pb_s_SI] [decimal](18, 6) NULL,
	[pb_c_SI] [decimal](18, 6) NULL,
	[pb_o_SL] [decimal](18, 6) NULL,
	[pb_s_SL] [decimal](18, 6) NULL,
	[pb_c_SL] [decimal](18, 6) NULL,
	[pb_o_KC] [decimal](18, 6) NULL,
	[pb_s_KC] [decimal](18, 6) NULL,
	[pb_c_KC] [decimal](18, 6) NULL,
	[pb_o_FC] [decimal](18, 6) NULL,
	[pb_s_FC] [decimal](18, 6) NULL,
	[pb_c_FC] [decimal](18, 6) NULL,
	[pb_o_FS] [decimal](18, 6) NULL,
	[pb_s_FS] [decimal](18, 6) NULL,
	[pb_c_FS] [decimal](18, 6) NULL,
	[pb_overall] [decimal](18, 6) NULL,
	[pb_stuff] [decimal](18, 6) NULL,
	[pb_command] [decimal](18, 6) NULL,
	[pb_xRV100] [decimal](18, 6) NULL,
	[pb_ERA] [decimal](18, 6) NULL,
	[sp_s_CH] [decimal](18, 6) NULL,
	[sp_l_CH] [decimal](18, 6) NULL,
	[sp_p_CH] [decimal](18, 6) NULL,
	[sp_s_CU] [decimal](18, 6) NULL,
	[sp_l_CU] [decimal](18, 6) NULL,
	[sp_p_CU] [decimal](18, 6) NULL,
	[sp_s_FF] [decimal](18, 6) NULL,
	[sp_l_FF] [decimal](18, 6) NULL,
	[sp_p_FF] [decimal](18, 6) NULL,
	[sp_s_SI] [decimal](18, 6) NULL,
	[sp_l_SI] [decimal](18, 6) NULL,
	[sp_p_SI] [decimal](18, 6) NULL,
	[sp_s_SL] [decimal](18, 6) NULL,
	[sp_l_SL] [decimal](18, 6) NULL,
	[sp_p_SL] [decimal](18, 6) NULL,
	[sp_s_KC] [decimal](18, 6) NULL,
	[sp_l_KC] [decimal](18, 6) NULL,
	[sp_p_KC] [decimal](18, 6) NULL,
	[sp_s_FC] [decimal](18, 6) NULL,
	[sp_l_FC] [decimal](18, 6) NULL,
	[sp_p_FC] [decimal](18, 6) NULL,
	[sp_s_FS] [decimal](18, 6) NULL,
	[sp_l_FS] [decimal](18, 6) NULL,
	[sp_p_FS] [decimal](18, 6) NULL,
	[sp_s_FO] [decimal](18, 6) NULL,
	[sp_l_FO] [decimal](18, 6) NULL,
	[sp_p_FO] [decimal](18, 6) NULL,
	[sp_stuff] [decimal](18, 6) NULL,
	[sp_location] [decimal](18, 6) NULL,
	[sp_pitching] [decimal](18, 6) NULL,
	[PPTV] [decimal](18, 6) NULL,
	[CPTV] [decimal](18, 6) NULL,
	[BPTV] [decimal](18, 6) NULL,
	[DSV] [decimal](18, 6) NULL,
	[DGV] [decimal](18, 6) NULL,
	[BTV] [decimal](18, 6) NULL,
	[rPPTV] [decimal](18, 6) NULL,
	[rCPTV] [decimal](18, 6) NULL,
	[rBPTV] [decimal](18, 6) NULL,
	[rDSV] [decimal](18, 6) NULL,
	[rDGV] [decimal](18, 6) NULL,
	[rBTV] [decimal](18, 6) NULL,
	[EBV] [decimal](18, 6) NULL,
	[ESV] [decimal](18, 6) NULL,
	[rFTeamV] [decimal](18, 6) NULL,
	[rBTeamV] [decimal](18, 6) NULL,
	[rTV] [decimal](18, 6) NULL,
	[pfxFA_Percent] [decimal](18, 6) NULL,
	[pfxFT_Percent] [decimal](18, 6) NULL,
	[pfxFC_Percent] [decimal](18, 6) NULL,
	[pfxFS_Percent] [decimal](18, 6) NULL,
	[pfxFO_Percent] [decimal](18, 6) NULL,
	[pfxSI_Percent] [decimal](18, 6) NULL,
	[pfxSL_Percent] [decimal](18, 6) NULL,
	[pfxCU_Percent] [decimal](18, 6) NULL,
	[pfxKC_Percent] [decimal](18, 6) NULL,
	[pfxEP_Percent] [decimal](18, 6) NULL,
	[pfxCH_Percent] [decimal](18, 6) NULL,
	[pfxSC_Percent] [decimal](18, 6) NULL,
	[pfxKN_Percent] [decimal](18, 6) NULL,
	[pfxUN_Percent] [decimal](18, 6) NULL,
	[pfxvFA] [decimal](18, 6) NULL,
	[pfxvFT] [decimal](18, 6) NULL,
	[pfxvFC] [decimal](18, 6) NULL,
	[pfxvFS] [decimal](18, 6) NULL,
	[pfxvFO] [decimal](18, 6) NULL,
	[pfxvSI] [decimal](18, 6) NULL,
	[pfxvSL] [decimal](18, 6) NULL,
	[pfxvCU] [decimal](18, 6) NULL,
	[pfxvKC] [decimal](18, 6) NULL,
	[pfxvEP] [decimal](18, 6) NULL,
	[pfxvCH] [decimal](18, 6) NULL,
	[pfxvSC] [decimal](18, 6) NULL,
	[pfxvKN] [decimal](18, 6) NULL,
	[pfxFA_X] [decimal](18, 6) NULL,
	[pfxFT_X] [decimal](18, 6) NULL,
	[pfxFC_X] [decimal](18, 6) NULL,
	[pfxFS_X] [decimal](18, 6) NULL,
	[pfxFO_X] [decimal](18, 6) NULL,
	[pfxSI_X] [decimal](18, 6) NULL,
	[pfxSL_X] [decimal](18, 6) NULL,
	[pfxCU_X] [decimal](18, 6) NULL,
	[pfxKC_X] [decimal](18, 6) NULL,
	[pfxEP_X] [decimal](18, 6) NULL,
	[pfxCH_X] [decimal](18, 6) NULL,
	[pfxSC_X] [decimal](18, 6) NULL,
	[pfxKN_X] [decimal](18, 6) NULL,
	[pfxFA_Z] [decimal](18, 6) NULL,
	[pfxFT_Z] [decimal](18, 6) NULL,
	[pfxFC_Z] [decimal](18, 6) NULL,
	[pfxFS_Z] [decimal](18, 6) NULL,
	[pfxFO_Z] [decimal](18, 6) NULL,
	[pfxSI_Z] [decimal](18, 6) NULL,
	[pfxSL_Z] [decimal](18, 6) NULL,
	[pfxCU_Z] [decimal](18, 6) NULL,
	[pfxKC_Z] [decimal](18, 6) NULL,
	[pfxEP_Z] [decimal](18, 6) NULL,
	[pfxCH_Z] [decimal](18, 6) NULL,
	[pfxSC_Z] [decimal](18, 6) NULL,
	[pfxKN_Z] [decimal](18, 6) NULL,
	[pfxwFA] [decimal](18, 6) NULL,
	[pfxwFT] [decimal](18, 6) NULL,
	[pfxwFC] [decimal](18, 6) NULL,
	[pfxwFS] [decimal](18, 6) NULL,
	[pfxwFO] [decimal](18, 6) NULL,
	[pfxwSI] [decimal](18, 6) NULL,
	[pfxwSL] [decimal](18, 6) NULL,
	[pfxwCU] [decimal](18, 6) NULL,
	[pfxwKC] [decimal](18, 6) NULL,
	[pfxwEP] [decimal](18, 6) NULL,
	[pfxwCH] [decimal](18, 6) NULL,
	[pfxwSC] [decimal](18, 6) NULL,
	[pfxwKN] [decimal](18, 6) NULL,
	[pfxwFA_PerC] [decimal](18, 6) NULL,
	[pfxwFT_PerC] [decimal](18, 6) NULL,
	[pfxwFC_PerC] [decimal](18, 6) NULL,
	[pfxwFS_PerC] [decimal](18, 6) NULL,
	[pfxwFO_PerC] [decimal](18, 6) NULL,
	[pfxwSI_PerC] [decimal](18, 6) NULL,
	[pfxwSL_PerC] [decimal](18, 6) NULL,
	[pfxwCU_PerC] [decimal](18, 6) NULL,
	[pfxwKC_PerC] [decimal](18, 6) NULL,
	[pfxwEP_PerC] [decimal](18, 6) NULL,
	[pfxwCH_PerC] [decimal](18, 6) NULL,
	[pfxwSC_PerC] [decimal](18, 6) NULL,
	[pfxwKN_PerC] [decimal](18, 6) NULL,
	[pfxO_SwingPercent] [decimal](18, 6) NULL,
	[pfxZ_SwingPercent] [decimal](18, 6) NULL,
	[pfxSwingPercent] [decimal](18, 6) NULL,
	[pfxO_ContactPercent] [decimal](18, 6) NULL,
	[pfxZ_ContactPercent] [decimal](18, 6) NULL,
	[pfxContactPercent] [decimal](18, 6) NULL,
	[pfxZonePercent] [decimal](18, 6) NULL,
	[pfxPace] [decimal](18, 6) NULL,
	[piCH_Percent] [decimal](18, 6) NULL,
	[piCS_Percent] [decimal](18, 6) NULL,
	[piCU_Percent] [decimal](18, 6) NULL,
	[piFA_Percent] [decimal](18, 6) NULL,
	[piFC_Percent] [decimal](18, 6) NULL,
	[piFS_Percent] [decimal](18, 6) NULL,
	[piKN_Percent] [decimal](18, 6) NULL,
	[piSB_Percent] [decimal](18, 6) NULL,
	[piSI_Percent] [decimal](18, 6) NULL,
	[piSL_Percent] [decimal](18, 6) NULL,
	[piXX_Percent] [decimal](18, 6) NULL,
	[pivCH] [decimal](18, 6) NULL,
	[pivCS] [decimal](18, 6) NULL,
	[pivCU] [decimal](18, 6) NULL,
	[pivFA] [decimal](18, 6) NULL,
	[pivFC] [decimal](18, 6) NULL,
	[pivFS] [decimal](18, 6) NULL,
	[pivKN] [decimal](18, 6) NULL,
	[pivSB] [decimal](18, 6) NULL,
	[pivSI] [decimal](18, 6) NULL,
	[pivSL] [decimal](18, 6) NULL,
	[pivXX] [decimal](18, 6) NULL,
	[piCH_X] [decimal](18, 6) NULL,
	[piCS_X] [decimal](18, 6) NULL,
	[piCU_X] [decimal](18, 6) NULL,
	[piFA_X] [decimal](18, 6) NULL,
	[piFC_X] [decimal](18, 6) NULL,
	[piFS_X] [decimal](18, 6) NULL,
	[piKN_X] [decimal](18, 6) NULL,
	[piSB_X] [decimal](18, 6) NULL,
	[piSI_X] [decimal](18, 6) NULL,
	[piSL_X] [decimal](18, 6) NULL,
	[piXX_X] [decimal](18, 6) NULL,
	[piCH_Z] [decimal](18, 6) NULL,
	[piCS_Z] [decimal](18, 6) NULL,
	[piCU_Z] [decimal](18, 6) NULL,
	[piFA_Z] [decimal](18, 6) NULL,
	[piFC_Z] [decimal](18, 6) NULL,
	[piFS_Z] [decimal](18, 6) NULL,
	[piKN_Z] [decimal](18, 6) NULL,
	[piSB_Z] [decimal](18, 6) NULL,
	[piSI_Z] [decimal](18, 6) NULL,
	[piSL_Z] [decimal](18, 6) NULL,
	[piXX_Z] [decimal](18, 6) NULL,
	[piwCH] [decimal](18, 6) NULL,
	[piwCS] [decimal](18, 6) NULL,
	[piwCU] [decimal](18, 6) NULL,
	[piwFA] [decimal](18, 6) NULL,
	[piwFC] [decimal](18, 6) NULL,
	[piwFS] [decimal](18, 6) NULL,
	[piwKN] [decimal](18, 6) NULL,
	[piwSB] [decimal](18, 6) NULL,
	[piwSI] [decimal](18, 6) NULL,
	[piwSL] [decimal](18, 6) NULL,
	[piwXX] [decimal](18, 6) NULL,
	[piwCH_PerC] [decimal](18, 6) NULL,
	[piwCS_PerC] [decimal](18, 6) NULL,
	[piwCU_PerC] [decimal](18, 6) NULL,
	[piwFA_PerC] [decimal](18, 6) NULL,
	[piwFC_PerC] [decimal](18, 6) NULL,
	[piwFS_PerC] [decimal](18, 6) NULL,
	[piwKN_PerC] [decimal](18, 6) NULL,
	[piwSB_PerC] [decimal](18, 6) NULL,
	[piwSI_PerC] [decimal](18, 6) NULL,
	[piwSL_PerC] [decimal](18, 6) NULL,
	[piwXX_PerC] [decimal](18, 6) NULL,
	[piO_SwingPercent] [decimal](18, 6) NULL,
	[piZ_SwingPercent] [decimal](18, 6) NULL,
	[piSwingPercent] [decimal](18, 6) NULL,
	[piO_ContactPercent] [decimal](18, 6) NULL,
	[piZ_ContactPercent] [decimal](18, 6) NULL,
	[piContactPercent] [decimal](18, 6) NULL,
	[piZonePercent] [decimal](18, 6) NULL,
	[piPace] [decimal](18, 6) NULL,
	[Events] [decimal](10, 1) NULL,
	[EV] [decimal](18, 6) NULL,
	[LA] [decimal](18, 6) NULL,
	[Barrels] [decimal](10, 1) NULL,
	[BarrelPercent] [decimal](18, 6) NULL,
	[maxEV] [decimal](18, 6) NULL,
	[HardHit] [decimal](10, 1) NULL,
	[HardHitPercent] [decimal](18, 6) NULL,
	[Q] [decimal](18, 6) NULL,
	[TG] [decimal](10, 1) NULL,
	[TIP] [decimal](10, 1) NULL,
	[PlayerNameRoute] [nvarchar](100) NULL,
	[PlayerName] [nvarchar](100) NULL,
	[position] [nvarchar](10) NULL,
	[TeamName] [nvarchar](100) NULL,
	[TeamNameAbb] [nvarchar](10) NULL,
	[teamid] [int] NULL,
	[playerid] [int] NULL,
 CONSTRAINT [PK_FactSeasonStatsPitching] PRIMARY KEY CLUSTERED 
(
	[FactSeasonStatsID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[FactSeasonProjections] ADD  DEFAULT (getdate()) FOR [ProjectionCycle]
GO
ALTER TABLE [dbo].[FactSeasonProjections]  WITH CHECK ADD  CONSTRAINT [FK_FactSeasonProjections_Player] FOREIGN KEY([PlayerID])
REFERENCES [dbo].[DimPlayer] ([PlayerID])
GO
ALTER TABLE [dbo].[FactSeasonProjections] CHECK CONSTRAINT [FK_FactSeasonProjections_Player]
GO
ALTER TABLE [dbo].[FactSeasonProjections]  WITH CHECK ADD  CONSTRAINT [FK_FactSeasonProjections_Season] FOREIGN KEY([SeasonID])
REFERENCES [dbo].[DimSeason] ([SeasonID])
GO
ALTER TABLE [dbo].[FactSeasonProjections] CHECK CONSTRAINT [FK_FactSeasonProjections_Season]
GO
ALTER TABLE [dbo].[FactSeasonProjections]  WITH CHECK ADD  CONSTRAINT [FK_FactSeasonProjections_Team] FOREIGN KEY([TeamID])
REFERENCES [dbo].[DimTeam] ([TeamID])
GO
ALTER TABLE [dbo].[FactSeasonProjections] CHECK CONSTRAINT [FK_FactSeasonProjections_Team]
GO
ALTER TABLE [dbo].[FactSeasonStatsBatting]  WITH CHECK ADD  CONSTRAINT [FK_FactSeasonStats_Player] FOREIGN KEY([PlayerID])
REFERENCES [dbo].[DimPlayer] ([PlayerID])
GO
ALTER TABLE [dbo].[FactSeasonStatsBatting] CHECK CONSTRAINT [FK_FactSeasonStats_Player]
GO
ALTER TABLE [dbo].[FactSeasonStatsBatting]  WITH CHECK ADD  CONSTRAINT [FK_FactSeasonStats_Season] FOREIGN KEY([SeasonID])
REFERENCES [dbo].[DimSeason] ([SeasonID])
GO
ALTER TABLE [dbo].[FactSeasonStatsBatting] CHECK CONSTRAINT [FK_FactSeasonStats_Season]
GO
ALTER TABLE [dbo].[FactSeasonStatsBatting]  WITH CHECK ADD  CONSTRAINT [FK_FactSeasonStats_Team] FOREIGN KEY([TeamID])
REFERENCES [dbo].[DimTeam] ([TeamID])
GO
ALTER TABLE [dbo].[FactSeasonStatsBatting] CHECK CONSTRAINT [FK_FactSeasonStats_Team]
GO
USE [master]
GO
ALTER DATABASE [Baseball] SET  READ_WRITE 
GO
