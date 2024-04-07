
/*
last modification: 02/04/24
Description: JavaScript logic for the front end of tree management webapp
*/


var mainMap, modalMap, chosenLocation;
var isInDeleteMode = false; // Flag to indicate delete mode state
var selectedTreeMarker = null; // Store the currently selected marker for deletion

function initializeModalMap() {
  if (!modalMap) {
    modalMap = L.map("treeLocationMap").setView([19.0211, 72.8710], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(modalMap);

    var geocoder = L.Control.geocoder({
      defaultMarkGeocode: false,
      placeholder: "Search for location...",
      showResultIcons: true,
    }).addTo(modalMap);

    geocoder.on("markgeocode", function (e) {
      var latlng = e.geocode.center;
      modalMap.setView(latlng, 16); // Zoom to the geocoder result
      if (chosenLocation) {
        modalMap.removeLayer(chosenLocation);
      }
      chosenLocation = L.marker(latlng).addTo(modalMap);
    });

    modalMap.on("click", function (e) {
      if (chosenLocation) {
        modalMap.removeLayer(chosenLocation);
      }
      chosenLocation = L.marker(e.latlng).addTo(modalMap);
    });
  } else {
    modalMap.invalidateSize();
  }
}
document.addEventListener("DOMContentLoaded", function () {
  mainMap = L.map("map").setView([19.0211, 72.8710], 17);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors",
  }).addTo(mainMap);

  populateTreeTypeDropdown();
  fetchInitialTreeData();

  document
    .getElementById("filterForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();
      applyFilters();
    });

  document
    .getElementById("submitTreeButton")
    .addEventListener("click", function (event) {
      // This will handle the submission
      submitTreeData();
    });

  $("#addTreeModal").on("shown.bs.modal", function () {
    initializeModalMap();
  });

  document
    .getElementById("deleteTreeButton")
    .addEventListener("click", function () {
      isInDeleteMode = !isInDeleteMode; // Toggle delete mode
      if (isInDeleteMode) {
        alert("Delete mode activated. Click on a tree to delete.");
        mainMap.getContainer().style.cursor = "crosshair"; // Change cursor to indicate delete mode
      } else {
        mainMap.getContainer().style.cursor = ""; // Restore cursor
        if (selectedTreeMarker) {
          treesLayer.resetStyle(selectedTreeMarker); // Reset style if a tree was selected
          selectedTreeMarker = null;
        }
      }
    });
});

function populateTreeTypeDropdown() {
  fetch("http://localhost:5000/get_tree_types")
    .then((response) => response.json())
    .then((types) => {
      const select = document.getElementById("treeType");
      types.forEach((type) => {
        const option = document.createElement("option");
        option.value = type;
        option.textContent = type;
        select.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Could not load tree types:", error);
    });
}

function fetchInitialTreeData() {
  fetch("http://localhost:5000/get_tree_data")
    .then((response) => response.json())
    .then((data) => {
      var geoJsonLayer = L.geoJSON(data, {
        onEachFeature: function (feature, layer) {
          if (feature.properties && feature.properties.Type) {
            layer.bindPopup(
              "Type: " +
                feature.properties.Type +
                "<br>Height: " +
                feature.properties.Height +
                " m" +
                "<br>Age: " +
                feature.properties.Age +
                " years"
            );
          }
        },
      }).addTo(mainMap);
      mainMap.fitBounds(geoJsonLayer.getBounds());
    })
    .catch((error) => {
      console.error("Error fetching tree data:", error);
    });
}

function applyFilters() {
  var filters = {
    treeType: document.getElementById("treeType").value,
    minAge: document.getElementById("minAge").value,
    maxAge: document.getElementById("maxAge").value,
    minHeight: document.getElementById("minHeight").value,
    maxHeight: document.getElementById("maxHeight").value,
  };
  fetchFilteredTreeData(filters);
}

function fetchFilteredTreeData(filters) {
  mainMap.eachLayer(function (layer) {
    if (!(layer instanceof L.TileLayer)) {
      mainMap.removeLayer(layer);
    }
  });

  fetch("http://localhost:5000/get_filtered_tree_data", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(filters),
  })
    .then((response) => response.json())
    .then((data) => {
      L.geoJSON(data, {
        onEachFeature: function (feature, layer) {
          if (feature.properties && feature.properties.Type) {
            layer.bindPopup(
              "Type: " +
                feature.properties.Type +
                "<br>Height: " +
                feature.properties.Height +
                " m" +
                "<br>Age: " +
                feature.properties.Age +
                " years"
            );
          }
        },
      }).addTo(mainMap);
      mainMap.fitBounds(geoJsonLayer.getBounds());
    })
    .catch((error) => {
      console.error("Error fetching filtered tree data:", error);
    });
}

// function submitTreeData() {
//   // Log to indicate function has been called
//   console.log("submitTreeData called");

//   var lat = chosenLocation ? chosenLocation.getLatLng().lat : null;
//   var lng = chosenLocation ? chosenLocation.getLatLng().lng : null;

//   // Check if the coordinates are selected
//   if (!lat || !lng) {
//     console.log("No location selected.");
//     alert("Please select a location on the map.");
//     return;
//   }

//   var treeData = {
//     name: document.getElementById("treeName").value,
//     age: parseInt(document.getElementById("treeAge").value, 10),
//     height: parseFloat(document.getElementById("treeHeight").value),
//     latitude: lat,
//     longitude: lng,
//   };

//   console.log("Submitting tree data:", treeData);

//   fetch("http://localhost:5000/add_tree", {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json",
//     },
//     body: JSON.stringify(treeData),
//   })
//     .then((response) => {
//       // Log the response status
//       console.log("Response status:", response.status);
//       if (!response.ok) {
//         throw new Error("Network response was not ok");
//       }
//       return response.json();
//     })
//     .then((data) => {
//       // Log the response data
//       console.log("Response data:", data);
//       if (data.status === "success") {
//         alert("Tree added successfully");
//         $("#addTreeModal").modal("hide");
//         fetchInitialTreeData();
//       } else {
//         alert("Failed to add tree: " + data.message);
//       }
//     })
//     .catch((error) => {
//       // Log any error that occurs during the fetch call
//       console.error("Error adding tree:", error);
//       alert("Error adding tree: " + error.message);
//     });
// }

function submitTreeData() {
  // Log to indicate function has been called
  console.log("submitTreeData called");

  var lat = chosenLocation ? chosenLocation.getLatLng().lat : null;
  var lng = chosenLocation ? chosenLocation.getLatLng().lng : null;

  // Check if the coordinates are selected
  if (!lat || !lng) {
    console.log("No location selected.");
    alert("Please select a location on the map.");
    return;
  }

  var treeData = {
    name: document.getElementById("treeName").value,
    height: parseFloat(document.getElementById("treeHeight").value),
    age: parseInt(document.getElementById("treeAge").value, 10),
    latitude: lat,
    longitude: lng,
  };

  console.log("Submitting tree data:", treeData);

  fetch("http://localhost:5000/add_tree", {  // Change the endpoint to vote_for_tree
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(treeData),
  })
    .then((response) => {
      // Log the response status
      console.log("Response status:", response.status);
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      // Log the response data
      console.log("Response data:", data);
      if (data.status === "success") {
        alert("Vote recorded successfully");
        $("#addTreeModal").modal("hide");
        fetchInitialTreeData();
      } else {
        alert("Failed to record vote: " + data.message);
      }
    })
    .catch((error) => {
      // Log any error that occurs during the fetch call
      console.error("Error recording vote:", error);
      alert("Error recording vote: " + error.message);
    });
}

setTimeout(function () {
  var geocoder = L.Control.geocoder({
    defaultMarkGeocode: false,
    placeholder: "Search for places",
    errorMessage: "Nothing found.",
  }).addTo(mainMap);

  geocoder.on("markgeocode", function (e) {
    var bbox = e.geocode.bbox;
    var poly = L.polygon([
      bbox.getSouthEast(),
      bbox.getNorthEast(),
      bbox.getNorthWest(),
      bbox.getSouthWest(),
    ]).addTo(mainMap);
    mainMap.fitBounds(poly.getBounds());
  });
}, 1000); // Delays the execution by 1000 milliseconds

function createAndAddMarker(treeData) {
  var marker = L.marker([treeData.latitude, treeData.longitude], {
    treeId: treeData.id,
  }).addTo(treesLayer);
  marker.on("click", function () {
    if (isInDeleteMode) {
      if (selectedTreeMarker) {
        selectedTreeMarker.setStyle({ color: "#3388ff" }); // Reset previous selection if exists
      }
      selectedTreeMarker = this;
      selectedTreeMarker.setStyle({ color: "#ff0000" }); // Highlight selected tree

      if (confirm("Are you sure you want to delete this tree?")) {
        deleteTree(selectedTreeMarker.options.treeId);
      } else {
        // Optionally reset style if user cancels deletion
        selectedTreeMarker.setStyle({ color: "#3388ff" });
        selectedTreeMarker = null;
      }
    }
  });
}

function deleteTree(treeId) {
  fetch("http://localhost:5000/delete_tree", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // Include authentication headers if needed
    },
    body: JSON.stringify({ tree_id: treeId }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        alert("Tree successfully deleted.");
        treesLayer.removeLayer(selectedTreeMarker); // Remove the marker from the map
        selectedTreeMarker = null; // Reset the selected marker
      } else {
        alert("Failed to delete tree: " + data.message);
      }
    })
    .catch((error) => {
      console.error("Error deleting tree:", error);
      alert("An error occurred while deleting the tree.");
    });
}