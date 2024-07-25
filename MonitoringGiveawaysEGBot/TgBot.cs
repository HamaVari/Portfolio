using Telegram.Bot.Types.Enums;
using Telegram.Bot.Types;
using Telegram.Bot;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;
using System.Globalization;

namespace MonitoringGiveawaysEGBot
{
    public class TgBot : ITgBot
    {
        private DateTime lastModified;

        public async Task CheckFileAsync(ITelegramBotClient botClient, long chatId, string filePath)
        {
            DateTime currentModified = System.IO.File.GetLastWriteTime(filePath);

            if (currentModified > lastModified)
            {
                lastModified = currentModified;

                string json = System.IO.File.ReadAllText(filePath);

                var gamesData = JsonConvert.DeserializeObject<JObject>(json);

                JArray? offersNow = (JArray?)gamesData?["offers_now"];
                JArray? upcomingOffers = (JArray?)gamesData?["upcoming_offers"];

                if (offersNow != null && upcomingOffers != null)
                {
                    bool sendWithSound = true;

                    foreach (var game in offersNow)
                    {
                        DateTime endDate = DateTime.ParseExact(game["EndDate"]?.ToString() ?? "", "dd.MM.yyyy HH:mm:ss", CultureInfo.InvariantCulture);

                        var caption = $"<b>Название: </b>{game["Title"]}\n" +
                                      $"<b>Описание: </b> {game["Description"]}\n" +
                                      $"<a href='{game["StoreLink"]}'>Ссылка на страницу в магазине</a>\n" +
                                      $"<b>Дата окончания раздачи: </b>{endDate.ToString("Раздача продлится до dd MMMM HH:mm по EET(Восточно-европейское время)")}\n";

                        var mediaGroupOffersNow = new IAlbumInputMedia[]
                        {
                            new InputMediaPhoto($"{game["ImageUrl"]}"),
                            new InputMediaVideo($"file://{game["VideoTrailer"]}") { Caption = $"<b><u>СЕЙЧАС РАЗДАЕТСЯ</u></b>\n\n{caption}", ParseMode = ParseMode.Html, SupportsStreaming = true },
                        };

                        if (sendWithSound)
                        {
                            await botClient.SendMediaGroupAsync(chatId, mediaGroupOffersNow);
                        }
                        else
                        {
                            await botClient.SendMediaGroupAsync(chatId, mediaGroupOffersNow, true);
                        }

                        sendWithSound = false;
                    }

                    string? message = null;

                    foreach (var game in upcomingOffers)
                    {
                        DateTime startDate = DateTime.ParseExact(game["EndDate"]?.ToString() ?? "", "dd.MM.yyyy HH:mm:ss", CultureInfo.InvariantCulture);

                        message += $"<b>{game["Title"]}</b> - " +
                                $"<a href='{game["StoreLink"]}'>cсылка на страницу в магазине</a>\n" +
                                $"{startDate.ToString("Раздача начнется с dd MMMM HH:mm по EET(Восточно-европейское время)")}\n\n";
                    }

                    if (message != null)
                    {
                        await botClient.SendTextMessageAsync(chatId, $"<b><u>АНОНС БУДУЩИХ РАЗДАЧ</u></b>\n\n{message}", ParseMode.Html, disableWebPagePreview: true);
                    }
                }
            }
        }
    }
}

