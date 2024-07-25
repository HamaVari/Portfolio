using Telegram.Bot;

namespace MonitoringGiveawaysEGBot
{
    public class Program
    {
        static async Task Main()
        {
            string url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=ru&country=UA&allowCountries=UA";
            var parser = new Parser();

            var bot = new TgBot();
            var botToken = //"Ваш_токен_бота";
            var optionsBot = new TelegramBotClientOptions(botToken, baseUrl: "http://localhost:8081");
            var botClient = new TelegramBotClient(optionsBot);

            long chatId = -1001957493617;
            string filePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "Data", "GamesData", "games_data.json").Replace('\\', Path.DirectorySeparatorChar);

            while (true)
            {
                parser.CheckWebsiteForChanges(url);
                await bot.CheckFileAsync(botClient, chatId, filePath);
                await Task.Delay(TimeSpan.FromDays(1));
            }
        }
    }
}