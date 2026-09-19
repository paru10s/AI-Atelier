import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./immersive.css";

const API = "http://127.0.0.1:8000";

const visualLibrary = [
  { src: "/kohler/editorial-room (3).png" },
  { src: "/kohler/faucets (3).png" },
  { src: "/kohler/green-room (3).png" },
  { src: "/kohler/wellness-room (3).png" },
  { src: "/kohler/bathroom-01.jpg" },
  { src: "/kohler/bathroom-02.jpg" },
  { src: "/kohler/bathroom-03.jpg" },
  { src: "/kohler/bathroom-04.jpg" },
  { src: "/kohler/bathroom-05.jpg" },
  { src: "/kohler/bathroom-06.jpg" },
  { src: "/kohler/bathroom-07.jpg" },
  { src: "/kohler/bathroom-08.jpg" },
  { src: "/kohler/bathroom-09.jpg" },
  { src: "/kohler/bathroom-10.jpg" },
  { src: "/kohler/bathroom-11.jpg" },
  { src: "/kohler/bathroom-12.jpg" },
  { src: "/kohler/bathroom-13.jpg" },
  { src: "/kohler/bathroom-14.jpg" },
  { src: "/kohler/bathroom-15.jpg" },
  { src: "/kohler/bathroom-16.jpg" },
];


const moods = [
  { name: "Warm Minimal", image: "/kohler/bathroom-03.jpg", prompt: "Warm minimal luxury bathroom, soft neutral stone, natural wood, sculptural fixtures, calm daylight" },
  { name: "Bold Heritage", image: "/kohler/green-room (3).png", prompt: "Bold heritage luxury bathroom, deep green tile, dark wood vanity, brass fixtures, editorial character" },
  { name: "Wellness", image: "/kohler/wellness-room (3).png", prompt: "Wellness sanctuary bathroom, warm sculptural architecture, spa atmosphere, soft ambient lighting" },
  { name: "Editorial Luxe", image: "/kohler/editorial-room (3).png", prompt: "Editorial luxury bathroom, dark accents, elegant mirrors, refined vanity, dramatic architectural lighting" },
];

function numericPrice(value) {
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  const cleaned = String(value ?? "").replace(/[^0-9.-]/g, "");
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : 0;
}

function money(value) {
  const n = numericPrice(value);
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);
}

function generatedImageUrl(image) {
  const clean = String(image || "").replace(/\\/g, "/");
  const filename = clean.split("/").pop();
  return filename ? `${API}/images/${encodeURIComponent(filename)}` : "";
}




async function prepareBathroomPhotoForStability(file) {
  if (!file) {
    throw new Error("Choose a bathroom photo first.");
  }

  const readAsBase64 = (inputFile) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = () => {
        const result = String(reader.result || "");
        resolve(result.includes(",") ? result.split(",")[1] : result);
      };

      reader.onerror = () =>
        reject(new Error("Could not read the bathroom photo."));

      reader.readAsDataURL(inputFile);
    });

  const dimensions = await new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      const value = {
        width: img.naturalWidth,
        height: img.naturalHeight,
      };

      URL.revokeObjectURL(url);
      resolve(value);
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Could not inspect the bathroom photo."));
    };

    img.src = url;
  });

  const { width, height } = dimensions;

  if (width < 64 || height < 64) {
    throw new Error(
      "The bathroom photo is too small for Stability. Use an image at least 64 px on each side."
    );
  }

  const aspect = Math.max(width / height, height / width);

  if (aspect > 2.5) {
    throw new Error(
      "The bathroom photo is too panoramic for Stability Structure. Please crop it closer to the room first."
    );
  }

  // Stability Structure allows up to 9,437,184 pixels.
  // Stay slightly below the API ceiling.
  const maxPixels = 9_000_000;
  const totalPixels = width * height;

  if (totalPixels <= maxPixels) {
    return {
      imageBase64: await readAsBase64(file),
      mimeType: file.type || "image/jpeg",
    };
  }

  const scale = Math.sqrt(maxPixels / totalPixels);
  const outputWidth = Math.max(64, Math.floor(width * scale));
  const outputHeight = Math.max(64, Math.floor(height * scale));

  const sourceUrl = URL.createObjectURL(file);

  try {
    const image = await new Promise((resolve, reject) => {
      const img = new Image();

      img.onload = () => resolve(img);
      img.onerror = () =>
        reject(new Error("Could not resize the bathroom photo."));

      img.src = sourceUrl;
    });

    const canvas = document.createElement("canvas");
    canvas.width = outputWidth;
    canvas.height = outputHeight;

    const context = canvas.getContext("2d");

    if (!context) {
      throw new Error("Could not prepare the bathroom photo.");
    }

    context.drawImage(
      image,
      0,
      0,
      outputWidth,
      outputHeight
    );

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob(
        (result) => {
          if (result) resolve(result);
          else reject(new Error("Could not prepare the bathroom photo."));
        },
        "image/jpeg",
        0.94
      );
    });

    return {
      imageBase64: await readAsBase64(blob),
      mimeType: "image/jpeg",
    };
  } finally {
    URL.revokeObjectURL(sourceUrl);
  }
}

const PRODUCT_IMAGE_MAP = {
  "Brazn 58.4 cm Rectangular Vessel Bathroom Sink":
    "https://kohler.scene7.com/is/image/PAWEB/Template_PDP_PLP?$PDPDesktop$=&$product_src=is{PAWEB/aag43534_rgb}",
  "Composed Wall-mount Lavatory Faucet":
    "https://kohler.scene7.com/is/image/PAWEB/Template_PDP_PLP?$PDPDesktop$=&$product_src=is{PAWEB/aad40440_rgb}",
  "ModernLife One-piece Round-front Toilet with Skirted Trapway, Dual-flush":
    "https://kohler.scene7.com/is/image/PAWEB/Template_PDP_PLP?$PDPDesktop$=&$product_src=is{PAWEB/aad74889_rgb}",
};

const CATEGORY_IMAGE_FALLBACK = {
  basin: "/kohler/bathroom-03.jpg",
  faucet: "/kohler/faucets (3).png",
  toilet: "/kohler/bathroom-11.jpg",
  shower: "/kohler/bathroom-08.jpg",
  bathtub: "/kohler/wellness-room (3).png",
};

function productImage(product) {
  return (
    product?.image ||
    product?.image_url ||
    product?.imageUrl ||
    product?.thumbnail ||
    PRODUCT_IMAGE_MAP[product?.name] ||
    CATEGORY_IMAGE_FALLBACK[String(product?.category || "").toLowerCase()] ||
    "/kohler/bathroom-01.jpg"
  );
}

function FloatingHome({ onStart }) {
  const rowA = visualLibrary.slice(0, 10);
  const rowB = visualLibrary.slice(10, 20);

  return (
    <main className="home rolling-home">
      <nav className="topbar rolling-nav">
        <div className="brand-lockup">
          <img className="kohler-logo" src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Kohler_logo.svg/500px-Kohler_logo.svg.png" alt="KOHLER" />
        </div>
        <div className="top-center">AI ATELIER</div>
        <div className="kohler-ai-mark">KOHLER × AI</div>
      </nav>

      <section className="rolling-hero">
        <div className="rolling-title" aria-hidden="true">
          <span>DESIGN</span>
          <span className="outline-word">YOUR</span>
          <span>SPACE.</span>
        </div>

        <div className="rolling-stage">
          <div className="roll-row roll-left">
            <div className="roll-track unique-track track-a">
              {rowA.map((item, i) => <img key={`a-${i}`} src={item.src} alt="" />)}
            </div>
          </div>
          <div className="roll-row roll-right">
            <div className="roll-track unique-track track-b">
              {rowB.map((item, i) => <img key={`b-${i}`} src={item.src} alt="" />)}
            </div>
          </div>
        </div>

        <div className="hero-focus">
          <div className="eyebrow">KOHLER × ARTIFICIAL INTELLIGENCE</div>
          <h1>YOUR BATHROOM.<br/><em>DESIGNED AROUND YOU.</em></h1>
          <button className="brand-cta" onClick={onStart}>
            <span>START DESIGNING</span>
            <span className="brand-cta-arrow">↗</span>
          </button>
          <p>ENTER YOUR SPACE · SET YOUR BUDGET · CHOOSE YOUR STYLE</p>
        </div>
        <div className="hero-fade"/>
      </section>

      <section className="rolling-statement">
        <p>REAL KOHLER PRODUCTS · PERSONALIZED SPACES · AI-POWERED VISUALIZATION</p>
        <h2>BOLD. BEAUTIFUL.<br/><em>BREATHTAKING BATHROOMS.</em></h2>
      </section>

      <section className="professional-cta refined-final">
        <div className="final-kicker">KOHLER × AI BATHROOM DESIGNER</div>
        <h2>MAKE THE ROOM<br/><em>YOUR OWN.</em></h2>
        <button onClick={onStart} className="brand-cta brand-cta-light">
          <span>START DESIGNING</span>
          <span className="brand-cta-arrow">↗</span>
        </button>
      </section>
    </main>
  );
}


function ExperienceTransition() {
  return (
    <div className="experience-transition" aria-hidden="true">
      <div className="transition-strip strip-one">
        <img src="/kohler/bathroom-04.jpg" alt="" />
      </div>
      <div className="transition-strip strip-two">
        <img src="/kohler/bathroom-11.jpg" alt="" />
      </div>
      <div className="transition-strip strip-three">
        <img src="/kohler/bathroom-15.jpg" alt="" />
      </div>

      <div className="transition-veil" />

      <div className="transition-center">
        <img
          className="transition-logo"
          src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Kohler_logo.svg/500px-Kohler_logo.svg.png"
          alt=""
        />
        <span>KOHLER × AI</span>
        <h2>YOUR SPACE<br/><em>IS TAKING SHAPE.</em></h2>
        <div className="transition-line"><i /></div>
        <small>SPACE · BUDGET · AESTHETIC · CREATE</small>
      </div>
    </div>
  );
}

function Studio({ onHome }) {
  const [step, setStep] = useState(-1);
  const [width, setWidth] = useState("12");
  const [depth, setDepth] = useState("10");
  const [budget, setBudget] = useState("600000");
  const [theme, setTheme] = useState(moods[0].prompt);
  const [selectedMood, setSelectedMood] = useState(0);
  const [image, setImage] = useState(null);
  const [products, setProducts] = useState([]);
  const [totalProductCost, setTotalProductCost] = useState(0);
  const [remainingBudget, setRemainingBudget] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [layout, setLayout] = useState(null);
  const [explorerOptions, setExplorerOptions] = useState([]);
  const [explorerLoading, setExplorerLoading] = useState(false);
  const [assistantText, setAssistantText] = useState("");
  const [assistantReply, setAssistantReply] = useState("");
  const [assistantSuggestion, setAssistantSuggestion] = useState(null);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [bathroomPhoto, setBathroomPhoto] = useState(null);
  const [bathroomPhotoPreview, setBathroomPhotoPreview] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [photoRedesign, setPhotoRedesign] = useState(null);
  const [photoRedesignLoading, setPhotoRedesignLoading] = useState(false);
  const [photoRedesignError, setPhotoRedesignError] = useState("");

  const roomDetails = useMemo(
    () => `Bathroom ${width} ft width x ${depth} ft depth`,
    [width, depth]
  );

  const calculatedProductTotal = useMemo(
    () => products.reduce((sum, product) => sum + numericPrice(product?.price), 0),
    [products]
  );

  const displayedProductTotal = calculatedProductTotal > 0
    ? calculatedProductTotal
    : numericPrice(totalProductCost);

  const displayedRemainingBudget = Math.max(
    numericPrice(budget) - displayedProductTotal,
    0
  );

  const chooseMood = (i) => {
    setSelectedMood(i);
    setTheme(moods[i].prompt);
  };

  const goToStep = (nextStep) => {
    setStep(nextStep);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const loadExplorer = async (runBudget = budget, runTheme = theme) => {
    setExplorerLoading(true);
    try {
      const response = await axios.post(`${API}/explore`, {
        room: roomDetails,
        budget: String(runBudget),
        style: runTheme,
      });
      setExplorerOptions(response.data?.options || []);
    } catch (error) {
      console.error("EXPLORER ERROR:", error);
      setExplorerOptions([]);
    } finally {
      setExplorerLoading(false);
    }
  };

  const askAssistant = async () => {
    const text = assistantText.trim();
    if (!text) return;

    setAssistantLoading(true);
    setAssistantReply("");
    setAssistantSuggestion(null);

    try {
      const response = await axios.post(`${API}/design-assistant`, {
        message: text,
        room: roomDetails,
        budget: String(budget),
        style: theme,
      });

      const data = response.data;
      setAssistantReply(data?.message || "Suggestion prepared.");

      if (data?.changed) {
        setAssistantSuggestion({
          budget: String(data.budget),
          style: data.style,
        });
      }
    } catch (error) {
      setAssistantReply(
        error?.response?.data?.detail ||
        "The design assistant could not process that request."
      );
    } finally {
      setAssistantLoading(false);
    }
  };

  const applyAssistantSuggestion = () => {
    if (!assistantSuggestion) return;

    setBudget(assistantSuggestion.budget);
    setTheme(assistantSuggestion.style);
    setAssistantSuggestion(null);
    setAssistantReply("Applied to your design settings. Review them before generating again.");
    goToStep(3);
  };

  const chooseAnalysisMood = (recommendedStyle = "") => {
    const text = String(recommendedStyle || "").toLowerCase();

    let match = 0;
    if (text.includes("heritage") || text.includes("bold") || text.includes("classic")) match = 1;
    else if (text.includes("wellness") || text.includes("spa") || text.includes("zen")) match = 2;
    else if (text.includes("editorial") || text.includes("luxe") || text.includes("luxury")) match = 3;

    setSelectedMood(match);
    setTheme(moods[match].prompt);
  };

  const handleBathroomPhoto = (event) => {
    const file = event.target.files?.[0];
    setAnalysis(null);
    setAnalysisError("");

    if (!file) {
      setBathroomPhoto(null);
      setBathroomPhotoPreview("");
      return;
    }

    if (!file.type.startsWith("image/")) {
      setAnalysisError("Please choose a JPG, PNG or WEBP bathroom photo.");
      return;
    }

    if (file.size > 8 * 1024 * 1024) {
      setAnalysisError("Please use an image smaller than 8 MB.");
      return;
    }

    setBathroomPhoto(file);
    setBathroomPhotoPreview(URL.createObjectURL(file));
    setAnalysis(null);
    setAnalysisError("");
    setPhotoRedesign(null);
    setPhotoRedesignError("");
  };

  const generatePhotoRedesign = async (imageBase64, mimeType, analysisResult) => {
    if (photoRedesignLoading) return;

    setPhotoRedesignLoading(true);
    setPhotoRedesignError("");
    setPhotoRedesign(null);

    try {
      const response = await axios.post(`${API}/generate-photo-redesign`, {
        image_base64: imageBase64,
        mime_type: mimeType,
        recommended_style: analysisResult?.recommended_style || "",
        design_rationale: analysisResult?.design_rationale || "",
        improvements: analysisResult?.improvements || [],
      });

      if (!response.data?.success) {
        throw new Error(
          response.data?.message || "Bathroom redesign failed."
        );
      }

      setPhotoRedesign(response.data.image || null);
    } catch (error) {
      setPhotoRedesignError(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error.message ||
        "Bathroom redesign failed."
      );
    } finally {
      setPhotoRedesignLoading(false);
    }
  };

  const analyzeBathroom = async () => {
    if (!bathroomPhoto) {
      setAnalysisError("Choose a bathroom photo first.");
      return;
    }

    setAnalysisLoading(true);
    setAnalysisError("");
    setAnalysis(null);
    setPhotoRedesign(null);
    setPhotoRedesignError("");

    try {
      const imageBase64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = String(reader.result || "");
          resolve(result.includes(",") ? result.split(",")[1] : result);
        };
        reader.onerror = () => reject(new Error("Could not read the image."));
        reader.readAsDataURL(bathroomPhoto);
      });

      const response = await axios.post(`${API}/analyze-bathroom`, {
        image_base64: imageBase64,
        mime_type: bathroomPhoto.type || "image/jpeg",
      });

      if (!response.data?.success) {
        throw new Error(response.data?.message || "Bathroom analysis failed.");
      }

      const analysisResult = response.data.analysis;

      setAnalysis(analysisResult);
    } catch (error) {
      setAnalysisError(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error.message ||
        "Bathroom analysis failed."
      );
    } finally {
      setAnalysisLoading(false);
    }
  };

  const generate = async () => {
    setLoading(true);
    setMessage("");
    setStep(4);
    try {
      const response = await axios.post(`${API}/generate-design`, {
        room: roomDetails,
        budget: String(budget),
        style: theme,
      });
      const data = response.data;
      if (!data?.success) {
        setMessage(data?.message || "Design generation failed.");
        setStep(3);
        return;
      }
      setImage(data.image);
          setProducts(data.products || []);
      setTotalProductCost(data.total_product_cost || 0);
      setRemainingBudget(data.remaining_budget || 0);
      setLayout(data.layout || null);
      setStep(5);
      loadExplorer(budget, theme);
    } catch (error) {
      setMessage(error?.response?.data?.detail || error.message || "Unable to reach the design service.");
      setStep(3);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="studio">
      <nav className="studio-nav">
        <button className="logo-button nav-reset" onClick={onHome} aria-label="Back to home">
          <img className="kohler-logo kohler-logo-studio" src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Kohler_logo.svg/500px-Kohler_logo.svg.png" alt="KOHLER" />
        </button>
        <div className="studio-progress">
          {["SPACE","BUDGET","AESTHETIC","CREATE"].map((x, i) => (
            <button
              type="button"
              key={x}
              onClick={() => goToStep(i)}
              className={step === i ? "active" : step > i ? "done" : ""}
            >
              {x}
            </button>
          ))}
        </div>
        <button className="text-button" onClick={onHome}>EXIT ×</button>
      </nav>

      {step === -1 && (
        <section className="studio-screen entry-choice-screen">
          <div className="entry-choice-copy">
            <span className="mini">BEGIN YOUR DESIGN</span>
            <h1>START WITH<br/><em>YOUR SPACE.</em></h1>
            <p>Choose how you want Kohler × AI to understand your bathroom.</p>
          </div>

          <div className="entry-choice-grid">
            <button
              type="button"
              className="entry-choice-card"
              onClick={() => goToStep(0)}
            >
              <img src="/kohler/bathroom-06.jpg" alt="" />
              <div className="entry-choice-shade" />
              <div className="entry-choice-card-copy">
                <span>01 / FROM DIMENSIONS</span>
                <h2>DESIGN A<br/><em>NEW SPACE.</em></h2>
                <p>Enter your room size and build the bathroom from scratch.</p>
                <b>ENTER ROOM DIMENSIONS ↗</b>
              </div>
            </button>

            <button
              type="button"
              className="entry-choice-card"
              onClick={() => {
                setAnalysisError("");
                document.getElementById("bathroom-photo-input")?.click();
              }}
            >
              <img src="/kohler/bathroom-12.jpg" alt="" />
              <div className="entry-choice-shade" />
              <div className="entry-choice-card-copy">
                <span>02 / FROM A PHOTO</span>
                <h2>ANALYZE MY<br/><em>BATHROOM.</em></h2>
                <p>Upload your existing bathroom and let AI understand it first.</p>
                <b>UPLOAD BATHROOM PHOTO ↗</b>
              </div>
            </button>
          </div>

          <input
            id="bathroom-photo-input"
            className="hidden-photo-input"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleBathroomPhoto}
          />

          {(bathroomPhotoPreview || analysisLoading || analysis || analysisError) && (
            <section className="bathroom-analyzer-panel">
              <div className="bathroom-analyzer-photo">
                {bathroomPhotoPreview && (
                  <img src={bathroomPhotoPreview} alt="Uploaded bathroom" />
                )}
                <span>YOUR EXISTING BATHROOM</span>
              </div>

              <div className="bathroom-analyzer-content">
                {!analysis && !analysisLoading && (
                  <>
                    <span className="mini">AI BATHROOM ANALYSIS</span>
                    <h2>READY TO<br/><em>UNDERSTAND IT.</em></h2>
                    <p>
                      Gemini will inspect visible fixtures, materials, lighting, storage
                      and the overall design direction, then create a redesigned concept
                      from this same bathroom photograph.
                    </p>

                    {analysisError && <div className="analyzer-error">{analysisError}</div>}

                    <div className="analyzer-actions">
                      <button className="analyze-primary" onClick={analyzeBathroom}>
                        ANALYZE THIS BATHROOM <b>↗</b>
                      </button>
                      <button
                        className="analyze-secondary"
                        onClick={() => document.getElementById("bathroom-photo-input")?.click()}
                      >
                        CHOOSE ANOTHER PHOTO
                      </button>
                    </div>
                  </>
                )}

                {analysisLoading && (
                  <div className="analysis-loading-state">
                    <span>GEMINI VISION</span>
                    <h2>READING<br/><em>THE ROOM.</em></h2>
                    <div className="analysis-loader"><i /></div>
                    <p>Detecting fixtures → reading materials → identifying opportunities</p>
                  </div>
                )}

                {analysis && !analysisLoading && (
                  <div className="analysis-result">
                    <span className="mini">YOUR BATHROOM, UNDERSTOOD</span>
                    <h2>{analysis.current_style || "EXISTING SPACE"}<br/><em>ANALYSIS.</em></h2>

                    <div className="analysis-result-grid">
                      <article>
                        <span>DETECTED</span>
                        <div className="analysis-pills">
                          {(analysis.detected_fixtures || []).map((item) => (
                            <b key={item}>{item}</b>
                          ))}
                        </div>
                      </article>

                      <article>
                        <span>MATERIALS + FINISHES</span>
                        <p>{(analysis.materials || []).join(" · ") || "Not confidently identified"}</p>
                      </article>

                      <article>
                        <span>LIGHTING</span>
                        <p>{analysis.lighting || "Not confidently identified"}</p>
                      </article>

                      <article>
                        <span>STORAGE</span>
                        <p>{analysis.storage || "Not confidently identified"}</p>
                      </article>
                    </div>

                    <div className="analysis-observations">
                      <span>DESIGN OPPORTUNITIES</span>
                      {(analysis.improvements || []).map((item, index) => (
                        <div key={`${item}-${index}`}>
                          <b>{String(index + 1).padStart(2, "0")}</b>
                          <p>{item}</p>
                        </div>
                      ))}
                    </div>

                    <div className="analysis-direction">
                      <span>AI-SUGGESTED DIRECTION</span>
                      <h3>{analysis.recommended_style || "Warm Minimal"}</h3>
                      <p>{analysis.design_rationale}</p>

                      <div className="analysis-categories">
                        {(analysis.recommended_categories || []).map((item) => (
                          <b key={item}>{item}</b>
                        ))}
                      </div>
                    </div>

                    <div className="analysis-note">
                      AI analysis is based only on what is visible in the uploaded image.
                      Room dimensions and hidden construction conditions are not inferred.
                    </div>

                    <section className="gemini-photo-redesign">
                      <div className="gemini-photo-redesign-head">
                        <span>STABILITY PHOTO REDESIGN</span>
                        <h3>YOUR EXISTING SPACE.<br/><em>REIMAGINED.</em></h3>
                        <p>
                          This concept is generated directly from the bathroom photo you uploaded.
                        </p>
                      </div>

                      {photoRedesignLoading && (
                        <div className="gemini-redesign-loading">
                          <span>STABILITY AI</span>
                          <b>CREATING REDESIGN...</b>
                          <div className="analysis-loader"><i /></div>
                        </div>
                      )}

                      {photoRedesignError && !photoRedesignLoading && (
                        <div className="analyzer-error">
                          {photoRedesignError}
                        </div>
                      )}

                      {photoRedesign && !photoRedesignLoading && (
                        <div className="gemini-redesign-image">
                          <img
                            src={generatedImageUrl(photoRedesign)}
                            alt="Redesigned bathroom concept"
                          />
                          <span>STABILITY / PHOTO-BASED REDESIGN CONCEPT</span>
                        </div>
                      )}


                      {!photoRedesignLoading && (
                        <button
                          type="button"
                          className="analyze-secondary regenerate-gemini-redesign"
                          onClick={async () => {
                            if (!bathroomPhoto || !analysis || photoRedesignLoading) return;

                            try {
                              const prepared = await prepareBathroomPhotoForStability(
                                bathroomPhoto
                              );

                              await generatePhotoRedesign(
                                prepared.imageBase64,
                                prepared.mimeType,
                                analysis
                              );
                            } catch (error) {
                              setPhotoRedesignError(
                                error?.message ||
                                "Could not prepare the bathroom photo."
                              );
                            }
                          }}
                        >
                          {photoRedesign
                            ? "GENERATE ANOTHER REDESIGN ↗"
                            : "GENERATE REDESIGN ↗"}
                        </button>
                      )}
                    </section>

                    <div className="analyzer-actions">
                      <button
                        className="analyze-primary"
                        onClick={() => {
                          setBathroomPhoto(null);
                          setBathroomPhotoPreview("");
                          setAnalysis(null);
                          setAnalysisError("");
                          setPhotoRedesign(null);
                          setPhotoRedesignError("");
                        }}
                      >
                        DONE WITH ANALYSIS <b>✓</b>
                      </button>
                      <button
                        className="analyze-secondary"
                        onClick={() => document.getElementById("bathroom-photo-input")?.click()}
                      >
                        ANALYZE ANOTHER PHOTO
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          <button className="back" onClick={onHome}>← BACK</button>
        </section>
      )}

      {step === 0 && (
        <section className="studio-screen space-screen clean-space-screen">
          <div className="screen-copy clean-space-copy">
            <span className="mini">YOUR SPACE</span>
            <h1>TELL US ABOUT<br/><em>THE ROOM.</em></h1>
            <p className="space-helper">ENTER THE INTERNAL ROOM DIMENSIONS IN FEET.</p>
          </div>

          <div className="dimension-editor clean-dimensions">
            <label>
              <span>WIDTH / FEET</span>
              <div className="dimension-value">
                <input value={width} onChange={(e) => setWidth(e.target.value)} inputMode="decimal" aria-label="Room width in feet" />
                <small>FT</small>
              </div>
            </label>

            <b className="dimension-x">×</b>

            <label>
              <span>DEPTH / FEET</span>
              <div className="dimension-value">
                <input value={depth} onChange={(e) => setDepth(e.target.value)} inputMode="decimal" aria-label="Room depth in feet" />
                <small>FT</small>
              </div>
            </label>
          </div>

          <figure className="space-visual">
            <img src="/kohler/bathroom-05.jpg" alt="" />
          </figure>

          <button className="back" onClick={() => goToStep(-1)}>← BACK</button>
          <button className="next studio-primary-next" onClick={() => goToStep(1)}>CONTINUE <b>→</b></button>
        </section>
      )}

      {step === 1 && (
        <section className="studio-screen budget-screen">
          <div className="screen-copy">
            <span className="mini">YOUR BUDGET</span>
            <h1>SET THE<br/><em>BOUNDARY.</em></h1>
          </div>
          <div className="budget-editor">
            <span>₹</span>
            <input value={budget} onChange={(e) => setBudget(e.target.value.replace(/\D/g,""))} />
            <small>₹ {money(budget)}</small>
            <input
              className="range"
              type="range"
              min="100000"
              max="2000000"
              step="50000"
              value={Math.min(Math.max(Number(budget || 100000),100000),2000000)}
              onChange={(e) => setBudget(e.target.value)}
            />
            <div className="range-labels"><span>₹1L</span><span>₹20L</span></div>
          </div>
          <figure className="studio-photo photo-two"><img src="/kohler/bathroom-08.jpg" alt="" /></figure>
          <button className="back" onClick={() => goToStep(0)}>← BACK</button>
          <button className="next" onClick={() => goToStep(2)}>CONTINUE <b>→</b></button>
        </section>
      )}

      {step === 2 && (
        <section className="studio-screen mood-screen">
          <div className="screen-copy compact">
            <span className="mini">YOUR AESTHETIC</span>
            <h1>WHAT FEELS<br/><em>LIKE YOU?</em></h1>
          </div>
          <div className="mood-grid">
            {moods.map((m, i) => (
              <button className={`mood ${selectedMood === i ? "selected" : ""}`} key={m.name} onClick={() => chooseMood(i)}>
                <img src={m.image} alt={m.name} />
                <span>{String(i+1).padStart(2,"0")} / {m.name}</span>
              </button>
            ))}
          </div>
          <div className="custom-theme">
            <label>OR DESCRIBE YOUR OWN VISION</label>
            <textarea value={theme} onChange={(e) => setTheme(e.target.value)} />
          </div>
          <button className="back" onClick={() => goToStep(1)}>← BACK</button>
          <button className="next" onClick={() => goToStep(3)}>CONTINUE <b>→</b></button>
        </section>
      )}

      {step === 3 && (
        <section className="studio-screen review-screen">
          <div className="review-left">
            <span className="mini">READY TO CREATE</span>
            <h1>YOUR ROOM.<br/><em>YOUR RULES.</em></h1>
            <p>We’ll use your dimensions, budget and aesthetic to curate the product set and visualize the bathroom.</p>
            {message && <div className="error">{message}</div>}
            <button className="generate" onClick={generate}>GENERATE MY BATHROOM <b>↗</b></button>
          </div>
          <div className="review-spec">
            <div><span>SPACE</span><strong>{width} × {depth} FT</strong></div>
            <div><span>BUDGET</span><strong>₹ {money(budget)}</strong></div>
            <div><span>AESTHETIC</span><strong>{moods[selectedMood]?.name || "CUSTOM"}</strong></div>
          </div>
          <button className="back" onClick={() => goToStep(2)}>← BACK</button>
        </section>
      )}

      {step === 4 && (
        <section className="loading-screen">
          <div className="loading-photo"><img src="/kohler/bathroom-13.jpg" alt="" /></div>
          <div className="loading-wash" />
          <div className="loading-copy">
            <span>AI DESIGN STUDIO</span>
            <h1>CREATING<br/><em>YOUR SPACE.</em></h1>
            <div className="loader-line"><i /></div>
            <p>Curating products → composing the room → creating visualization</p>
          </div>
        </section>
      )}

      {step === 5 && (
        <section className="result">
          <div className="result-head">
            <div>
              <span className="mini">YOUR PERSONALIZED SPACE</span>
              <h1>{moods[selectedMood]?.name || "CUSTOM"}<br/><em>BATHROOM.</em></h1>
            </div>
            <div className="result-meta">
              <span>{width} × {depth} FT</span>
              <span>₹ {money(budget)} BUDGET</span>
            </div>
          </div>

          <div className="result-image">
            <img src={generatedImageUrl(image)} alt="Generated bathroom design" />
            <span>AI VISUALIZATION / CONCEPT IMAGE</span>
          </div>

          <div className="result-actions">
            <button onClick={() => goToStep(2)}>← REDESIGN</button>
            <button onClick={onHome}>BACK TO EXPERIENCE ↗</button>
          </div>

          <section className="explorer-section">
            <div className="explorer-heading">
              <span>BUDGET TRADE-OFF EXPLORER</span>
              <h2>SEE WHAT YOUR<br/><em>BUDGET CAN DO.</em></h2>
              <p>
                Compare three Kohler product directions without spending another image-generation credit.
              </p>
            </div>

            {explorerLoading ? (
              <div className="explorer-loading">BUILDING PRODUCT OPTIONS...</div>
            ) : (
              <div className="explorer-grid">
                {explorerOptions.map((option) => (
                  <article className="explorer-card" key={option.label}>
                    <div className="explorer-card-top">
                      <span>{option.label}</span>
                      <strong>₹ {money(option.budget)}</strong>
                    </div>
                    <div className="explorer-cost">
                      <span>SELECTED PRODUCTS</span>
                      <strong>₹ {money(option.cost)}</strong>
                    </div>
                    <div className="explorer-products">
                      {(option.products || []).map((product) => (
                        <div key={`${option.label}-${product.category}-${product.name}`}>
                          <span>{product.category}</span>
                          <p>{product.name}</p>
                        </div>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="assistant-section">
            <div className="assistant-copy">
              <span>KOHLER × AI DESIGN ASSISTANT</span>
              <h2>REFINE IT<br/><em>WITH WORDS.</em></h2>
              <p>
                Try “make it warmer”, “make it more luxurious”, “reduce my budget”,
                or “set the budget to 5 lakh”.
              </p>
            </div>

            <div className="assistant-panel">
              <textarea
                value={assistantText}
                onChange={(e) => setAssistantText(e.target.value)}
                placeholder="Describe the change you want..."
              />

              <button onClick={askAssistant} disabled={assistantLoading}>
                {assistantLoading ? "THINKING..." : "ASK DESIGN ASSISTANT"} <b>↗</b>
              </button>

              {assistantReply && (
                <div className="assistant-reply">
                  <p>{assistantReply}</p>

                  {assistantSuggestion && (
                    <div className="assistant-preview">
                      <div>
                        <span>PROPOSED BUDGET</span>
                        <strong>₹ {money(assistantSuggestion.budget)}</strong>
                      </div>
                      <div>
                        <span>PROPOSED AESTHETIC</span>
                        <strong>{assistantSuggestion.style}</strong>
                      </div>

                      <button onClick={applyAssistantSuggestion}>
                        APPLY TO DESIGN SETTINGS →
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          <section className="product-section refined-products">
            <div className="product-heading">
              <span>CURATED FOR YOUR SPACE</span>
              <h2>THE PRODUCT<br/><em>SELECTION.</em></h2>
              <p>Real Kohler fixtures selected to fit your space, aesthetic and project budget.</p>
            </div>

            <div className="product-list">
              {products.map((p, i) => (
                <article className="product-row" key={`${p.name}-${i}`}>
                  <div className="product-category">{p.category || "KOHLER"}</div>

                  <div className="product-image-wrap">
                    <img
                      src={productImage(p)}
                      alt={p.name || "Kohler product"}
                      className="product-image"
                      onError={(e) => {
                        e.currentTarget.onerror = null;
                        e.currentTarget.src =
                          CATEGORY_IMAGE_FALLBACK[String(p.category || "").toLowerCase()] ||
                          "/kohler/bathroom-01.jpg";
                      }}
                    />
                  </div>

                  <div className="product-copy">
                    <h3>{p.name || "Selected product"}</h3>
                  </div>

                  <div className="product-price">₹ {money(p.price)}</div>
                </article>
              ))}
            </div>
          </section>

          <section className="budget-ledger">
            <div className="ledger-title">
              <span>PROJECT OVERVIEW</span>
              <h2>BUDGET<br/><em>AT A GLANCE.</em></h2>
            </div>

            <div className="ledger-values">
              <div className="ledger-row">
                <span>PROJECT BUDGET</span>
                <strong>₹ {money(budget)}</strong>
              </div>
              <div className="ledger-row">
                <span>KOHLER PRODUCT SELECTION</span>
                <strong>₹ {money(displayedProductTotal)}</strong>
              </div>
              <div className="ledger-row ledger-balance">
                <span>REMAINING BUDGET</span>
                <strong>₹ {money(displayedRemainingBudget)}</strong>
              </div>
            </div>
          </section>
        </section>
      )}
    </main>
  );
}

export default function App() {
  const [page, setPage] = useState("home");
  const [transitioning, setTransitioning] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [page]);

  const enterStudio = () => {
    if (transitioning) return;
    setTransitioning(true);

    window.setTimeout(() => {
      setPage("studio");
    }, 1150);

    window.setTimeout(() => {
      setTransitioning(false);
    }, 2450);
  };

  return (
    <>
      {page === "home"
        ? <FloatingHome onStart={enterStudio} />
        : <Studio onHome={() => setPage("home")} />
      }
      {transitioning && <ExperienceTransition />}
    </>
  );
}
