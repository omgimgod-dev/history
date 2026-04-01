function initMap(places, isAdmin = false, onClickCallback = null) {
    const map = document.getElementById('city-map');
    const container = document.getElementById('map-container');
    if (!map || !container) return;

    if (!map.complete) {
        map.onload = start;
    } else {
        start();
    }

    function start() {
        // Получаем реальные размеры изображения
        const imageWidth = map.naturalWidth;
        const imageHeight = map.naturalHeight;

        // Контейнер для маркеров
        const markersContainer = document.createElement('div');
        markersContainer.style.position = 'absolute';
        markersContainer.style.top = '0';
        markersContainer.style.left = '0';
        markersContainer.style.width = '100%';
        markersContainer.style.height = '100%';
        markersContainer.style.zIndex = '1000';
        markersContainer.style.pointerEvents = 'none';
        container.appendChild(markersContainer);

        // Создаём маркеры с сохранением исходных координат
        const markers = places.map(place => {
            const marker = document.createElement('div');
            marker.className = 'marker';
            marker.style.position = 'absolute';
            marker.style.pointerEvents = 'auto';
            marker.setAttribute('data-id', place.id);
            marker.setAttribute('data-name', place.name);
            markersContainer.appendChild(marker);

            if (!isAdmin) {
                const tooltip = document.createElement('span');
                tooltip.className = 'marker-tooltip';
                tooltip.textContent = place.name;
                marker.appendChild(tooltip);
            }

            marker.addEventListener('click', (e) => {
                e.stopPropagation();
                window.location.href = '/places/place/' + place.id;
            });

            // Исходные координаты в пикселях исходного изображения
            return {
                element: marker,
                x: (place.x / 100) * imageWidth,
                y: (place.y / 100) * imageHeight
            };
        });

        // Функция обновления позиций маркеров с учётом текущего масштаба и смещения
        function updateMarkers() {
            const scale = window.mapScale || 1;
            const offsetX = window.mapOffsetX || 0;
            const offsetY = window.mapOffsetY || 0;

            markers.forEach(m => {
                const screenX = m.x * scale + offsetX;
                const screenY = m.y * scale + offsetY;
                m.element.style.left = screenX + 'px';
                m.element.style.top = screenY + 'px';
            });
        }

        // Делаем функцию доступной глобально, чтобы её можно было вызывать при каждом обновлении трансформации
        window.updateMarkers = updateMarkers;
        // Первоначальное обновление
        updateMarkers();

        // Двойной клик для администратора
        if (isAdmin && onClickCallback) {
            container.addEventListener('dblclick', (e) => {
                if (isDragging) return; // isDragging должна быть доступна глобально или передана
                const rect = container.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                const scale = window.mapScale || 1;
                const offsetX = window.mapOffsetX || 0;
                const offsetY = window.mapOffsetY || 0;

                // Координаты на исходном изображении (пиксели)
                const xImg = (mouseX - offsetX) / scale;
                const yImg = (mouseY - offsetY) / scale;
                // Переводим в проценты
                const xPercent = (xImg / imageWidth) * 100;
                const yPercent = (yImg / imageHeight) * 100;
                onClickCallback(xPercent, yPercent);
            });
        }
    }
}