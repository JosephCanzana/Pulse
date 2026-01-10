document.addEventListener("DOMContentLoaded", () => {
    const educationSelect = document.getElementById("educationSelect");
    const sectionSelectElement = document.getElementById("sectionSelect");

    if (!educationSelect || !sectionSelectElement) return;

    const sectionSelect = new TomSelect("#sectionSelect", {
        valueField: "id",
        labelField: "text",
        searchField: ["text"],
        create: false,
        placeholder: "Search and select a section...",
        load: function(query, callback) {
            const education_level_id = educationSelect.value;
            if (!education_level_id) return callback();

            fetch(`/admin/api/sections/search?education_level_id=${education_level_id}&q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => callback(data))
                .catch(() => callback());
        }
    });

    // Refresh sections when education level changes
    educationSelect.addEventListener("change", () => {
        sectionSelect.clearOptions();
        sectionSelect.clear(true);
    });

    // Preselect section in Edit form
    const preselectedSection = sectionSelectElement.dataset.selected;

    if (preselectedSection) {
        const education_level_id = educationSelect.value;
        if (education_level_id) {
            // Fetch all sections for this education level to populate dropdown
            fetch(`/admin/api/sections/search?education_level_id=${education_level_id}&q=`)
                .then(res => res.json())
                .then(data => {
                    data.forEach(option => sectionSelect.addOption(option));
                    sectionSelect.addItem(preselectedSection); // preselect now
                });
        }
    }
});
