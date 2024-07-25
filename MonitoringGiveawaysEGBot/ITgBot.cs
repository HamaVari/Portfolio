using Telegram.Bot;

namespace MonitoringGiveawaysEGBot
{
    public interface ITgBot
    {
        public Task CheckFileAsync(ITelegramBotClient botClient, long chatId, string filePath);
    }
}
