const coordinatesElement = document.getElementById('coordinates');
let coords;

const eventSource = new EventSource('http://127.0.0.1:8000/api/v1/event-stream/get-data');
eventSource.onopen = () => {
    console.log('EventSource connected')
    coordinatesElement.innerText = ''
}

eventSource.addEventListener('locationUpdate', function (event) {
    coords = JSON.parse(event.data);
    console.log('LocationUpdate', coords);
    updateCoordinates(coords)
});

eventSource.onerror = (error) => {
    console.error('EventSource failed', error)
     eventSource.close()
}

function updateCoordinates(coordinates) {
    const paragraph = document.createElement('p');
    paragraph.textContent = `Latitude: ${coordinates.lat}, Longitude: ${coordinates.lng}`;
    coordinatesElement.appendChild(paragraph);
}