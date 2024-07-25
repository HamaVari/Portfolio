using FFMpegCore;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;
using OpenQA.Selenium.Support.UI;
using MonitoringGiveawaysEGBot.Data;
using OpenQA.Selenium.DevTools;

namespace MonitoringGiveawaysEGBot
{
    public class Parser : IParser
    {
        private Game[]? _prev_games;

        public void CheckWebsiteForChanges(string url)
        {
            try
            {
                HttpClient client = new HttpClient();
                HttpResponseMessage response = client.GetAsync(url).Result;
                response.EnsureSuccessStatusCode();
                string json = response.Content.ReadAsStringAsync().Result;
                client.Dispose();

                JObject? jsonObj = JObject.Parse(json);

                int lastElement = jsonObj?.SelectToken("data.Catalog.searchStore.elements")?.Count() ?? 0;

                Game[]? games = new Game[lastElement - 2];

                for (int i = 0; i < games.Length; i++)
                {
                    var gameData = GetGameData(jsonObj, i + 1);
                    if (gameData != null)
                    {
                        games[i] = gameData;
                    }
                }

                List<Game>? gamesNow = new List<Game>();
                List<Game>? gamesUpcoming = new List<Game>();

                DateTime? timeUtc = DateTime.UtcNow;
                DateTime? KyivDateTime = ConvertUtcToKyivTimeZone(timeUtc);

                for (int i = 0; i < games.Length; i++)
                {
                    if (games[i] != null && (_prev_games?[i].Title != games[i].Title))
                    {
                        if (KyivDateTime >= games[i].StartDate)
                        {
                            gamesNow.Add(games[i]);
                        }
                        else
                        {
                            gamesUpcoming.Add(games[i]);
                        }
                    }
                }

                _prev_games = games;

                var gamesDataJson = new JObject()
                {
                    ["offers_now"] = JArray.FromObject(gamesNow),
                    ["upcoming_offers"] = JArray.FromObject(gamesUpcoming),
                };

                string filePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "Data", "GamesData", "games_data.json").Replace('\\', Path.DirectorySeparatorChar);
                File.WriteAllText(filePath, gamesDataJson.ToString());

                Console.WriteLine("\nСейчас раздаётся: ");
                foreach (var game in gamesNow)
                {
                    Console.WriteLine($"\nНазвание: {game.Title}" +
                                      $"\n{game.ImageUrl}" +
                                      $"\nОписание: {game.Description}" +
                                      $"\nСсылка на страницу в магазине: {game.StoreLink}" +
                                      $"\nДата окончания раздачи: {game.EndDate?.ToString("Раздача продлится до dd MMMM HH:mm по EET(Восточно-европейское время)")}" +
                                      $"\nТрейлер игры: {game.VideoTrailer}");
                }

                Console.WriteLine("\nАнонс будущих раздач: ");
                foreach (var game in gamesUpcoming)
                {
                    Console.WriteLine($"\nНазвание: {game.Title}" +
                                      $"\n{game.ImageUrl}" +
                                      $"\nОписание: {game.Description}" +
                                      $"\nСсылка на страницу в магазине: {game.StoreLink}" +
                                      $"\nДата начала раздачи: {game.StartDate?.ToString("Раздача начнется с dd MMMM HH:mm по EET(Восточно-европейское время)")}" +
                                      $"\nТрейлер игры: {game.VideoTrailer}");
                }
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Ошибка HTTP-запроса: {ex.Message}");
            }
            catch (JsonException ex)
            {
                Console.WriteLine($"Ошибка разбора JSON: {ex.Message}");
            }
            catch (FormatException ex)
            {
                Console.WriteLine($"Ошибка формата: {ex.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Неизвестная ошибка: {ex.Message}");
            }
        }

        public DateTime? ConvertUtcToKyivTimeZone(DateTime? time)
        {
            if (time == null)
            {
                return null;
            }

            try
            {
                var kyivTimeZone = TimeZoneInfo.FindSystemTimeZoneById("Europe/Kiev");
                var kyivDateTime = TimeZoneInfo.ConvertTimeFromUtc(time.Value, kyivTimeZone);
                return kyivDateTime;
            }
            catch (TimeZoneNotFoundException ex)
            {
                Console.WriteLine($"Возникла ошибка при попытке найти часовой пояс: {ex.Message}");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Неизвестная ошибка: {ex.Message}");
                return null;
            }
        }

        public Game? GetGameData(JObject? jsonObj, int index)
        {
            if (jsonObj == null)
            {
                return null;
            }

            try
            {
                JToken? gameObj = jsonObj?.SelectToken($"data.Catalog.searchStore.elements[{index}]") ?? null;
                JToken? promotionalOffer = gameObj?.SelectToken("promotions.promotionalOffers[0].promotionalOffers[0]") ?? gameObj?.SelectToken("promotions.upcomingPromotionalOffers[0].promotionalOffers[0]") ?? null;
                string? storeLink = $"https://store.epicgames.com/ru/p/{(string?)gameObj?.SelectToken("catalogNs.mappings[0].pageSlug")}" ?? null;

                return new Game
                {
                    Title = (string?)gameObj?.SelectToken("title") ?? null,
                    ImageUrl = (string?)gameObj?.SelectToken("keyImages[0].url") ?? null,
                    Description = (string?)gameObj?.SelectToken("description") ?? null,
                    StoreLink = storeLink,
                    VideoTrailer = GetGameTrailer(storeLink, index) ?? null,
                    StartDate = ConvertUtcToKyivTimeZone((DateTime?)promotionalOffer?.SelectToken("startDate")) ?? null,
                    EndDate = ConvertUtcToKyivTimeZone((DateTime?)promotionalOffer?.SelectToken("endDate")) ?? null,
                };
            }
            catch (ArgumentException ex)
            {
                Console.WriteLine($"Значение параметра index вне допустимого диапазона: {ex.Message}");
                return null;
            }
            catch (FormatException ex)
            {
                Console.WriteLine($"Ошибка формата: {ex.Message}");
                return null;
            }
            catch (JsonReaderException ex)
            {
                Console.WriteLine($"Входные данные не являются правильным форматом JSON и не удается десериализовать данные: {ex.Message}");
                return null;
            }
            catch (JsonSerializationException ex)
            {
                Console.WriteLine($"Возникла ошибка при сериализации или десериализации объектов JSON: {ex.Message}");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Неизвестная ошибка: {ex.Message}");
                return null;
            }
        }

        public string? GetGameTrailer(string? storeLink, int index)
        {
            if (storeLink == null)
            {
                return null;
            }

            try
            {
                List<string>? Links = GetVideoAudioFragmentLinks(storeLink);
                string? videoUrl = null;
                string? audioUrl = null;

                if (Links == null)
                {
                    Console.WriteLine("Не удалось загрузить файлы аудио и видео-фрагментов и обработать видео из-за отсутствия ссылок на файлы фрагментов");
                    return null;
                }

                foreach (string Link in Links)
                {
                    if (Link.EndsWith("high.fmp4"))
                    {
                        videoUrl = Link;
                    }
                    if (Link.EndsWith(".m4a"))
                    {
                        audioUrl = Link;
                    }
                }

                string videoFileName = "video.mp4";
                string audioFileName = "audio.m4a";
                string outputFileName = $"output{index}.mp4";

                string videoFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "Data", "GamesData", videoFileName).Replace('\\', Path.DirectorySeparatorChar);
                string audioFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "Data", "GamesData", audioFileName).Replace('\\', Path.DirectorySeparatorChar);
                string outputFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "Data", "GamesData", outputFileName).Replace('\\', Path.DirectorySeparatorChar);

                using (HttpClient client = new HttpClient())
                {
                    Console.WriteLine("Загрузка файла видео-фрагмента...");
                    HttpResponseMessage videoResponse = client.GetAsync(videoUrl).Result;
                    using (Stream videoStream = videoResponse.Content.ReadAsStream())
                    {
                        using (FileStream videoFile = new FileStream(videoFilePath, FileMode.Create))
                        {
                            videoStream.CopyTo(videoFile);
                        }
                    }
                    Console.WriteLine("Файл видео-фрагмента загружен!");

                    Console.WriteLine("Загрузка файла аудио-фрагмента...");
                    HttpResponseMessage audioResponse = client.GetAsync(audioUrl).Result;
                    using (Stream audioStream = audioResponse.Content.ReadAsStream())
                    {
                        using (FileStream audioFile = new FileStream(audioFilePath, FileMode.Create))
                        {
                            audioStream.CopyTo(audioFile);
                        }
                    }
                    Console.WriteLine("Файл аудио-фрагмента загружен!");

                    Console.WriteLine("Создание выходного полного видеофайла...");
                    using (FileStream outputFile = new FileStream(outputFilePath, FileMode.Create))
                    {
                        Console.WriteLine("Создан выходной полный видеофайл!");
                    }
                }

                string FFMpegPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "Data", "FFMpeg").Replace('\\', Path.DirectorySeparatorChar);

                GlobalFFOptions.Configure(options => options.BinaryFolder = FFMpegPath);
                FFMpeg.ReplaceAudio(videoFilePath, audioFilePath, outputFilePath);
                Console.WriteLine("Фрагменты видео и аудио успешно обработаны, полное видео сохранено в выходном файле!");

                return outputFilePath;
            }
            catch (AggregateException ex)
            {
                Console.WriteLine($"Произошла одна или несколько ошибок при выполнении асинхронной операции: {ex.Message}");
                return null;
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Ошибка при выполнении запроса к серверу для загрузки видео и аудио-фрагментов: {ex.Message}");
                return null;
            }
            catch (IOException ex)
            {
                Console.WriteLine($"Ошибка ввода-вывода при создании, открытии, записи или закрытии одного из файловых потоков: {ex.Message}");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Неизвестная ошибка: {ex.Message}");
                return null;
            }
        }

        public List<string>? GetVideoAudioFragmentLinks(string? storeLink)
        {
            try
            {
                string chromeDriverPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "Data", "ChromeDriver").Replace('\\', Path.DirectorySeparatorChar);
                var options = new ChromeOptions();
                options.AddArguments("--headless=new", "--disable-infobars", "--disable-extensions", "--disable-notifications", "--disable-background-timer-throttling", "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding");
                var driver = new ChromeDriver(chromeDriverPath, options);

                List<string>? xhrUrls = new List<string>();

                DevToolsSession session = driver.GetDevToolsSession();
                session.Domains.Network.EnableNetwork();
                session.DevToolsEventReceived += (sender, e) =>
                {
                    if (e.EventName == "requestWillBeSent")
                    {
                        string? url = e.EventData.SelectToken("request.url")?.ToString() ?? null;
                        if (url != null)
                        {
                            if (url.EndsWith(".fmp4") || url.EndsWith(".m4a"))
                            {
                                xhrUrls.Add(url);
                            }
                        }
                    }
                };

                driver.Navigate().GoToUrl(storeLink);
                driver.Manage().Timeouts().PageLoad = TimeSpan.FromSeconds(30);

                int maxWaitTime = 20;
                int waitedTime = 0;

                while (xhrUrls.Count(url => url.EndsWith("high.fmp4")) == 0 || xhrUrls.Count(url => url.EndsWith(".m4a")) == 0)
                {
                    if (waitedTime == maxWaitTime / 2)
                    {
                        Verify18Plus(driver);
                        if (xhrUrls.Count(url => url.EndsWith("high.fmp4")) == 0 || xhrUrls.Count(url => url.EndsWith(".m4a")) == 0)
                        {
                            SearchAVFragmentsInTabs(driver, xhrUrls);
                        }
                    }

                    if (waitedTime >= maxWaitTime)
                    {
                        Console.WriteLine($"Не удалось получить ссылки на видео и аудиофрагменты в течение {maxWaitTime} секунд.");
                        xhrUrls = null;
                        break;
                    }
                    waitedTime++;
                    Thread.Sleep(1000);
                }

                driver.Quit();

                if (xhrUrls != null)
                {
                    foreach (var url in xhrUrls)
                    {
                        Console.WriteLine(url);
                    }
                }
                return xhrUrls;
            }
            catch (DriverServiceNotFoundException ex)
            {
                Console.WriteLine($"Не удалось найти исполняемый файл драйвера браузера: {ex.Message}");
                return null;
            }
            catch (WebDriverException ex)
            {
                Console.WriteLine($"Возникли проблемы с запуском или использованием драйвера браузера: {ex.Message}");
                return null;
            }
            catch (InvalidOperationException ex)
            {
                Console.WriteLine($"Операция не может быть выполнена потому что браузер находится в некорректном состоянии: {ex.Message}");
                return null;
            }
            catch (TimeoutException ex)
            {
                Console.WriteLine($"Истекло время ожидания загрузки страницы сайта: {ex.Message}");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Неизвестная ошибка: {ex.Message}");
                return null;
            }
        }

        public void Verify18Plus(ChromeDriver driver)
        {
            try
            {
                WebDriverWait wait = new WebDriverWait(driver, TimeSpan.FromSeconds(10));

                IWebElement? buttonContinue = wait.Until(driver =>
                {
                    var element = driver.FindElement(By.CssSelector("button.css-1a6we1t"));
                    if (element.Displayed && element.Enabled)
                    {
                        return element;
                    }
                    return null;
                });

                if (buttonContinue == null)
                {
                    return;
                }

                buttonContinue.Click();
            }
            catch (NoSuchElementException ex)
            {
                Console.WriteLine($"Элемент с заданным селектором не найден на странице: {ex.Message}");
            }
            catch (WebDriverTimeoutException ex)
            {
                Console.WriteLine($"Элемент не появился на странице в течение заданного времени: {ex.Message}");
            }
            catch (WebDriverException ex)
            {
                Console.WriteLine($"Возникли проблемы с запуском или использованием драйвера браузера: {ex.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Неизвестная ошибка: {ex.Message}");
            }
        }

        public void SearchAVFragmentsInTabs(ChromeDriver driver, List<string>? xhrUrls)
        {
            try
            {
                WebDriverWait wait = new WebDriverWait(driver, TimeSpan.FromSeconds(10));
                IWebElement? elementUl = wait.Until(driver =>
                {
                    var element = driver.FindElement(By.XPath("//div[@data-testid='wrapper']//ul"));

                    if (element.Displayed && element.Enabled)
                    {
                        return element;
                    }
                    return null;
                });

                if (elementUl == null)
                {
                    return;
                }

                IList<IWebElement>? elementsLi = elementUl?.FindElements(By.TagName("li"));

                if (elementsLi == null)
                {
                    return;
                }

                bool nextSlideButtonClicked = false;

                foreach (IWebElement elementLi in elementsLi)
                {
                    IWebElement? elementButton = elementLi.FindElement(By.TagName("button"));
                    try
                    {
                        if (elementButton == null)
                        {
                            continue;
                        }

                        elementButton.Click();
                        Thread.Sleep(3000);
                        if (xhrUrls?.Count(url => url.EndsWith("high.fmp4")) != 0 && xhrUrls?.Count(url => url.EndsWith(".m4a")) != 0)
                        {
                            return;
                        }
                    }
                    catch (ElementNotInteractableException)
                    {
                        if (!nextSlideButtonClicked)
                        {
                            IWebElement? nextSlideButton = driver.FindElement(By.XPath("//*[@data-testid='nav-button']//button[@aria-label='Следующий слайд']"));

                            if (nextSlideButton == null)
                            {
                                return;
                            }

                            nextSlideButton.Click();
                            nextSlideButtonClicked = true;

                            wait = new WebDriverWait(driver, TimeSpan.FromSeconds(5));
                            elementButton = wait.Until(driver =>
                            {
                                if (elementButton.Displayed && elementButton.Enabled)
                                {
                                    elementButton.Click();
                                    Thread.Sleep(3000);
                                    return elementButton;
                                }
                                return null;
                            });
                            continue;
                        }
                    }
                    nextSlideButtonClicked = false;
                }
            }
            catch (NoSuchElementException ex)
            {
                Console.WriteLine($"Элемент с заданным селектором не найден на странице: {ex.Message}");
            }
            catch (WebDriverTimeoutException ex)
            {
                Console.WriteLine($"Элемент не появился на странице в течение заданного времени: {ex.Message}");
            }
            catch (WebDriverException ex)
            {
                Console.WriteLine($"Возникли проблемы с запуском или использованием драйвера браузера: {ex.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Неизвестная ошибка: {ex.Message}");
            }
        }
    }
}

