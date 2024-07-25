using Newtonsoft.Json.Linq;
using OpenQA.Selenium.Chrome;
using MonitoringGiveawaysEGBot.Data;

namespace MonitoringGiveawaysEGBot
{
    public interface IParser
    {
        public void CheckWebsiteForChanges(string url);
        public DateTime? ConvertUtcToKyivTimeZone(DateTime? time);
        public Game? GetGameData(JObject? jsonObj, int index);
        public string? GetGameTrailer(string? storeLink, int index);
        public List<string>? GetVideoAudioFragmentLinks(string? storeLink);
        public void Verify18Plus(ChromeDriver driver);
        public void SearchAVFragmentsInTabs(ChromeDriver driver, List<string>? xhrUrls);
    }
}
