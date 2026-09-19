import { useState } from "react";
import { Rnd } from "react-rnd";


function FloorPlanner({
  roomWidth,
  roomDepth,
  onSave
}) {

  // =====================================================
  // ROOM
  // =====================================================

  const SCALE = 55;

  const widthFt = Number(roomWidth);
  const depthFt = Number(roomDepth);

  const widthPx = widthFt * SCALE;
  const depthPx = depthFt * SCALE;


  // =====================================================
  // GRID
  // 0.25 ft = 13.75 px
  // =====================================================

  const GRID_FT = 0.25;
  const GRID_PX = GRID_FT * SCALE;


  // =====================================================
  // BATHTUB FEASIBILITY
  //
  // Current tub footprint:
  // 5.58 ft x 2.46 ft
  //
  // We also require enough room for circulation and
  // the other essential fixtures.
  // =====================================================

  const BATHTUB_WIDTH = 5.58;
  const BATHTUB_DEPTH = 2.46;

  const roomArea = widthFt * depthFt;


  const bathtubFits = (

    roomArea >= 55 &&

    (
      (
        widthFt >= 7.5 &&
        depthFt >= 6
      )
      ||
      (
        widthFt >= 6 &&
        depthFt >= 7.5
      )
    )

  );


  // =====================================================
  // FIXTURE STATE
  //
  // Positions and dimensions are stored in FEET.
  // =====================================================

  const [fixtures, setFixtures] = useState({

    basin: {

      x: 0.25,
      y: 0.25,

      width: 2,
      depth: 1.5

    },


    toilet: {

      x: Math.max(
        widthFt - 2.25,
        0.25
      ),

      y: 2.5,

      width: 2,
      depth: 2.3

    },


    shower: {

      x: 0.25,

      y: Math.max(
        depthFt - 3.25,
        0.25
      ),

      width: 3,
      depth: 3

    },


    bathtub: {

      x: Math.max(
        widthFt -
        BATHTUB_WIDTH -
        0.25,
        0.25
      ),

      y: Math.max(
        depthFt -
        BATHTUB_DEPTH -
        0.25,
        0.25
      ),

      width: BATHTUB_WIDTH,
      depth: BATHTUB_DEPTH

    }

  });


  // =====================================================
  // DOOR
  // =====================================================

  const [door, setDoor] = useState({

    position: Math.max(
      widthFt / 2 - 1.25,
      0
    )

  });


  // =====================================================
  // WINDOW
  // =====================================================

  const [
    windowPosition,
    setWindowPosition
  ] = useState({

    position: Math.max(
      widthFt / 2 - 1.5,
      0
    )

  });


  // =====================================================
  // HELPERS
  // =====================================================

  const feetToPixels = (feet) => {

    return feet * SCALE;

  };


  const pixelsToFeet = (pixels) => {

    return Number(
      (pixels / SCALE).toFixed(2)
    );

  };


  const snapFeet = (feet) => {

    return Number(

      (
        Math.round(
          feet / GRID_FT
        ) * GRID_FT
      ).toFixed(2)

    );

  };


  // =====================================================
  // MOVE FIXTURE
  // =====================================================

  const moveFixture = (
    name,
    pixelX,
    pixelY
  ) => {

    const x = snapFeet(
      pixelsToFeet(pixelX)
    );

    const y = snapFeet(
      pixelsToFeet(pixelY)
    );


    setFixtures(
      (previous) => ({

        ...previous,

        [name]: {

          ...previous[name],

          x,
          y

        }

      })
    );

  };


  // =====================================================
  // RESIZE FIXTURE
  // =====================================================

  const resizeFixture = (
    name,
    pixelWidth,
    pixelHeight,
    pixelX,
    pixelY
  ) => {

    let width = snapFeet(
      pixelsToFeet(pixelWidth)
    );

    let depth = snapFeet(
      pixelsToFeet(pixelHeight)
    );


    // -------------------------------------------------
    // BASIN LIMITS
    // -------------------------------------------------

    if (name === "basin") {

      width = Math.max(
        1.5,
        Math.min(width, 4)
      );

      depth = Math.max(
        1.25,
        Math.min(depth, 2.5)
      );

    }


    // -------------------------------------------------
    // SHOWER LIMITS
    // -------------------------------------------------

    if (name === "shower") {

      width = Math.max(
        2.5,
        Math.min(width, 5)
      );

      depth = Math.max(
        2.5,
        Math.min(depth, 5)
      );

    }


    const x = snapFeet(
      pixelsToFeet(pixelX)
    );

    const y = snapFeet(
      pixelsToFeet(pixelY)
    );


    setFixtures(
      (previous) => ({

        ...previous,

        [name]: {

          ...previous[name],

          x,
          y,
          width,
          depth

        }

      })
    );

  };


  // =====================================================
  // RECTANGLE OVERLAP
  // =====================================================

  const rectanglesOverlap = (
    a,
    b
  ) => {

    return !(

      a.x + a.width <= b.x ||

      b.x + b.width <= a.x ||

      a.y + a.depth <= b.y ||

      b.y + b.depth <= a.y

    );

  };


  // =====================================================
  // BUILD ACTIVE FIXTURE LIST
  // =====================================================

  const getActiveFixtures = () => {

    const active = {

      basin: {
        ...fixtures.basin
      },

      toilet: {
        ...fixtures.toilet
      },

      shower: {
        ...fixtures.shower
      }

    };


    if (bathtubFits) {

      active.bathtub = {
        ...fixtures.bathtub
      };

    }


    return active;

  };


  // =====================================================
  // BUILD SAVED LAYOUT
  // =====================================================

  const buildLayout = () => {

    const activeFixtures =
      getActiveFixtures();


    const savedFixtures = {};


    Object.entries(
      activeFixtures
    ).forEach(
      ([name, fixture]) => {

        savedFixtures[name] = {

          x: fixture.x,
          y: fixture.y,

          width: fixture.width,
          depth: fixture.depth,

          rotation: 0

        };

      }
    );


    return {

      room: {

        width: widthFt,
        depth: depthFt

      },


      fixtures:
        savedFixtures,


      door: {

        wall: "front",

        position:
          door.position,

        width: 2.5,

        swing: "inward"

      },


      window: {

        wall: "back",

        position:
          windowPosition.position,

        width: 3

      },


      bathtubIncluded:
        bathtubFits

    };

  };


  // =====================================================
  // VALIDATE LAYOUT
  // =====================================================

  const validateLayout = () => {

    const activeFixtures =
      getActiveFixtures();


    const items = Object.entries(
      activeFixtures
    );


    // -------------------------------------------------
    // CHECK ROOM BOUNDARIES
    // -------------------------------------------------

    for (
      const [name, fixture]
      of items
    ) {

      if (

        fixture.x < 0 ||

        fixture.y < 0 ||

        fixture.x +
        fixture.width >
        widthFt + 0.01 ||

        fixture.y +
        fixture.depth >
        depthFt + 0.01

      ) {

        return {

          valid: false,

          message:
            `${name} is outside the room.`

        };

      }

    }


    // -------------------------------------------------
    // CHECK OVERLAPS
    // -------------------------------------------------

    for (
      let i = 0;
      i < items.length;
      i++
    ) {

      for (
        let j = i + 1;
        j < items.length;
        j++
      ) {

        const [
          nameA,
          fixtureA
        ] = items[i];


        const [
          nameB,
          fixtureB
        ] = items[j];


        if (
          rectanglesOverlap(
            fixtureA,
            fixtureB
          )
        ) {

          return {

            valid: false,

            message:
              `${nameA} overlaps ${nameB}.`

          };

        }

      }

    }


    return {

      valid: true,

      message:
        "Layout valid."

    };

  };


  // =====================================================
  // SAVE
  // =====================================================

  const saveLayout = () => {

    const validation =
      validateLayout();


    if (!validation.valid) {

      alert(
        "Invalid layout: " +
        validation.message
      );

      return;

    }


    const savedLayout =
      buildLayout();


    console.log(
      "================================"
    );

    console.log(
      "SAVED USER LAYOUT"
    );

    console.log(
      "================================"
    );

    console.log(
      JSON.stringify(
        savedLayout,
        null,
        2
      )
    );


    if (onSave) {

      onSave(
        savedLayout
      );

    }


    alert(
      "Layout saved successfully!"
    );

  };


  // =====================================================
  // FIXTURE COMPONENT
  // =====================================================

  const Fixture = ({
    name,
    label,
    resizable = false
  }) => {

    const fixture =
      fixtures[name];


    return (

      <Rnd

        size={{

          width:
            feetToPixels(
              fixture.width
            ),

          height:
            feetToPixels(
              fixture.depth
            )

        }}

        position={{

          x:
            feetToPixels(
              fixture.x
            ),

          y:
            feetToPixels(
              fixture.y
            )

        }}

        bounds="parent"


        // ---------------------------------------------
        // SNAP MOVEMENT
        // ---------------------------------------------

        dragGrid={[
          GRID_PX,
          GRID_PX
        ]}


        // ---------------------------------------------
        // RESIZE
        // ---------------------------------------------

        enableResizing={
          resizable
        }


        resizeGrid={[
          GRID_PX,
          GRID_PX
        ]}


        minWidth={
          name === "shower"
            ? feetToPixels(2.5)
            : name === "basin"
            ? feetToPixels(1.5)
            : undefined
        }


        minHeight={
          name === "shower"
            ? feetToPixels(2.5)
            : name === "basin"
            ? feetToPixels(1.25)
            : undefined
        }


        maxWidth={
          name === "shower"
            ? feetToPixels(5)
            : name === "basin"
            ? feetToPixels(4)
            : undefined
        }


        maxHeight={
          name === "shower"
            ? feetToPixels(5)
            : name === "basin"
            ? feetToPixels(2.5)
            : undefined
        }


        onDragStop={(
          event,
          data
        ) => {

          moveFixture(
            name,
            data.x,
            data.y
          );

        }}


        onResizeStop={(
          event,
          direction,
          ref,
          delta,
          position
        ) => {

          if (!resizable) {
            return;
          }


          resizeFixture(

            name,

            ref.offsetWidth,

            ref.offsetHeight,

            position.x,

            position.y

          );

        }}


        style={{
          ...styles.fixture,

          cursor:
            resizable
              ? "move"
              : "move"
        }}

      >

        <div
          style={
            styles.fixtureContent
          }
        >

          <div
            style={
              styles.fixtureLabel
            }
          >

            {label}

          </div>


          <div
            style={
              styles.fixtureSize
            }
          >

            {fixture.width.toFixed(2)}
            {" × "}
            {fixture.depth.toFixed(2)}
            {" ft"}

          </div>


          {
            resizable &&

            <div
              style={
                styles.resizeText
              }
            >

              drag edges to resize

            </div>
          }

        </div>

      </Rnd>

    );

  };


  // =====================================================
  // UI
  // =====================================================

  return (

    <div
      style={
        styles.wrapper
      }
    >


      <h2
        style={
          styles.heading
        }
      >

        Bathroom Floor Planner

      </h2>


      <p
        style={
          styles.description
        }
      >

        Drag the fixtures to create
        your preferred bathroom layout.
        Resize the wash station and
        shower if required.

      </p>


      <div
        style={
          styles.dimensionText
        }
      >

        Room:
        {" "}
        {widthFt}
        {" ft × "}
        {depthFt}
        {" ft"}

        {" • "}

        {roomArea.toFixed(1)}
        {" sq ft"}

      </div>


      {/* ===============================================
          BATHTUB STATUS
      =============================================== */}

      {

        bathtubFits

        ? (

          <div
            style={
              styles.successMessage
            }
          >

            ✓ Room has sufficient space
            for the selected bathtub.

          </div>

        )

        : (

          <div
            style={
              styles.warningMessage
            }
          >

            Bathtub omitted — the room
            is too small for a practical
            bathtub layout. The design
            will use a shower instead.

          </div>

        )

      }


      {/* ===============================================
          ROOM
      =============================================== */}

      <div

        style={{

          ...styles.room,

          width:
            widthPx,

          height:
            depthPx

        }}

      >


        {/* =============================================
            WINDOW
        ============================================= */}

        <Rnd

          size={{

            width:
              3 * SCALE,

            height:
              12

          }}

          position={{

            x:
              feetToPixels(
                windowPosition.position
              ),

            y: 0

          }}

          bounds="parent"

          enableResizing={false}

          dragAxis="x"

          dragGrid={[
            GRID_PX,
            GRID_PX
          ]}

          onDragStop={(
            event,
            data
          ) => {

            setWindowPosition({

              position:
                snapFeet(
                  pixelsToFeet(
                    data.x
                  )
                )

            });

          }}

          style={
            styles.window
          }

        >

          WINDOW

        </Rnd>


        {/* =============================================
            WASH STATION
        ============================================= */}

        <Fixture

          name="basin"

          label="WASH STATION"

          resizable={true}

        />


        {/* =============================================
            TOILET
        ============================================= */}

        <Fixture

          name="toilet"

          label="TOILET"

        />


        {/* =============================================
            SHOWER
        ============================================= */}

        <Fixture

          name="shower"

          label="SHOWER"

          resizable={true}

        />


        {/* =============================================
            BATHTUB — ONLY WHEN FEASIBLE
        ============================================= */}

        {

          bathtubFits &&

          <Fixture

            name="bathtub"

            label="BATHTUB"

          />

        }


        {/* =============================================
            DOOR
        ============================================= */}

        <Rnd

          size={{

            width:
              2.5 * SCALE,

            height:
              14

          }}

          position={{

            x:
              feetToPixels(
                door.position
              ),

            y:
              depthPx - 14

          }}

          bounds="parent"

          enableResizing={false}

          dragAxis="x"

          dragGrid={[
            GRID_PX,
            GRID_PX
          ]}

          onDragStop={(
            event,
            data
          ) => {

            setDoor({

              position:
                snapFeet(
                  pixelsToFeet(
                    data.x
                  )
                )

            });

          }}

          style={
            styles.door
          }

        >

          DOOR

        </Rnd>


      </div>


      {/* ===============================================
          FIXTURE DETAILS
      =============================================== */}

      <div
        style={
          styles.fixtureDetails
        }
      >

        <strong>
          Current fixture sizes
        </strong>


        <span>

          Wash Station:
          {" "}
          {fixtures.basin.width}
          {" × "}
          {fixtures.basin.depth}
          {" ft"}

        </span>


        <span>

          Toilet:
          {" "}
          {fixtures.toilet.width}
          {" × "}
          {fixtures.toilet.depth}
          {" ft"}

        </span>


        <span>

          Shower:
          {" "}
          {fixtures.shower.width}
          {" × "}
          {fixtures.shower.depth}
          {" ft"}

        </span>


        {

          bathtubFits &&

          <span>

            Bathtub:
            {" "}
            {fixtures.bathtub.width}
            {" × "}
            {fixtures.bathtub.depth}
            {" ft"}

          </span>

        }

      </div>


      {/* ===============================================
          LEGEND
      =============================================== */}

      <div
        style={
          styles.legend
        }
      >

        <span>

          Wash Station =
          Basin + Faucet

        </span>


        <span>

          Wash Station and Shower
          can be resized.

        </span>


        <span>

          Toilet and Bathtub use
          fixed physical footprints.

        </span>


        <span>

          All movement and resizing
          snaps to 0.25 ft.

        </span>


        <span>

          Overlapping fixtures cannot
          be saved.

        </span>

      </div>


      {/* ===============================================
          SAVE
      =============================================== */}

      <button

        type="button"

        onClick={
          saveLayout
        }

        style={
          styles.saveButton
        }

      >

        Save Layout

      </button>


    </div>

  );

}


// =====================================================
// STYLES
// =====================================================

const styles = {

  wrapper: {

    marginTop: "30px",

    padding: "25px",

    background: "#f7f7f7",

    borderRadius: "16px",

    overflowX: "auto"

  },


  heading: {

    marginTop: 0,

    marginBottom: "8px"

  },


  description: {

    color: "#666",

    marginTop: 0

  },


  dimensionText: {

    fontWeight: "600",

    marginBottom: "15px"

  },


  successMessage: {

    background: "#edf8ef",

    border: "1px solid #b9dfc0",

    padding: "10px 14px",

    borderRadius: "8px",

    marginBottom: "20px",

    fontSize: "13px"

  },


  warningMessage: {

    background: "#fff4e5",

    border: "1px solid #efcf9d",

    padding: "10px 14px",

    borderRadius: "8px",

    marginBottom: "20px",

    fontSize: "13px"

  },


  room: {

    position: "relative",

    background: "#ffffff",

    border: "5px solid #222",

    boxSizing: "border-box",

    margin:
      "30px auto 40px auto",

    overflow: "hidden"

  },


  fixture: {

    border: "2px solid #222",

    background: "#e9eef3",

    borderRadius: "6px",

    display: "flex",

    alignItems: "center",

    justifyContent: "center",

    boxSizing: "border-box",

    zIndex: 2

  },


  fixtureContent: {

    display: "flex",

    flexDirection: "column",

    alignItems: "center",

    justifyContent: "center",

    pointerEvents: "none",

    userSelect: "none",

    padding: "4px"

  },


  fixtureLabel: {

    fontSize: "12px",

    fontWeight: "700",

    textAlign: "center"

  },


  fixtureSize: {

    marginTop: "3px",

    fontSize: "10px",

    color: "#555"

  },


  resizeText: {

    marginTop: "3px",

    fontSize: "8px",

    color: "#777"

  },


  door: {

    background: "#222",

    color: "white",

    fontSize: "10px",

    fontWeight: "700",

    display: "flex",

    alignItems: "center",

    justifyContent: "center",

    cursor: "ew-resize",

    zIndex: 10

  },


  window: {

    background: "#9edcff",

    border: "2px solid #222",

    fontSize: "9px",

    fontWeight: "700",

    display: "flex",

    alignItems: "center",

    justifyContent: "center",

    cursor: "ew-resize",

    zIndex: 10,

    boxSizing: "border-box"

  },


  fixtureDetails: {

    display: "flex",

    flexDirection: "column",

    gap: "4px",

    background: "white",

    border: "1px solid #ddd",

    padding: "12px",

    borderRadius: "8px",

    marginBottom: "15px",

    fontSize: "12px"

  },


  legend: {

    display: "flex",

    flexDirection: "column",

    gap: "5px",

    fontSize: "13px",

    color: "#666"

  },


  saveButton: {

    width: "100%",

    marginTop: "20px",

    padding: "14px",

    background: "#111",

    color: "white",

    border: "none",

    borderRadius: "10px",

    fontSize: "16px",

    fontWeight: "600",

    cursor: "pointer"

  }

};


export default FloorPlanner;