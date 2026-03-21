/**
 * Recipe photo: fixed 16:9 crop before upload (Cropper.js).
 * Expects: #file, .img-area, #recipeCropModal, #recipeCropImage, #recipeCropApply
 * Optional: #remove_image_field (edit page).
 */
(function () {
    var MAX_BYTES = 2 * 1024 * 1024;
    var ASPECT = 16 / 9;

    var cropper = null;
    var objectUrl = null;
    var cropApplied = false;
    /** Last successfully cropped blob (so Cancel on a re-pick does not wipe the previous upload). */
    var lastAcceptedBlob = null;

    function getInput() {
        return document.getElementById("file");
    }

    function getImgArea() {
        return document.querySelector(".img-area");
    }

    function getRemoveField() {
        return document.getElementById("remove_image_field");
    }

    function setPreviewFromBlob(blob) {
        var imgArea = getImgArea();
        if (!imgArea) return;
        imgArea.querySelectorAll("img").forEach(function (el) {
            el.remove();
        });
        var url = URL.createObjectURL(blob);
        var img = document.createElement("img");
        img.src = url;
        img.alt = "";
        imgArea.prepend(img);
        imgArea.classList.add("active");
        imgArea.dataset.img = "recipe-photo.jpg";
    }

    function assignFileToInput(blob) {
        var inputFile = getInput();
        var file = new File([blob], "recipe-photo.jpg", { type: "image/jpeg" });
        var dt = new DataTransfer();
        dt.items.add(file);
        inputFile.files = dt.files;
        lastAcceptedBlob = blob;
        var rf = getRemoveField();
        if (rf) rf.value = "";
    }

    /**
     * Try export at decreasing resolution / quality until <= MAX_BYTES or give up.
     */
    function exportUnderLimit(cropperInstance, callback) {
        var plans = [
            { w: 1200, h: 675, q: 0.88 },
            { w: 1200, h: 675, q: 0.72 },
            { w: 960, h: 540, q: 0.85 },
            { w: 960, h: 540, q: 0.65 },
            { w: 800, h: 450, q: 0.8 },
            { w: 800, h: 450, q: 0.55 }
        ];
        var i = 0;

        function next() {
            if (i >= plans.length) {
                callback(null);
                return;
            }
            var p = plans[i];
            i += 1;
            var canvas = cropperInstance.getCroppedCanvas({
                width: p.w,
                height: p.h,
                imageSmoothingQuality: "high"
            });
            canvas.toBlob(function (blob) {
                if (!blob) {
                    next();
                    return;
                }
                if (blob.size <= MAX_BYTES) {
                    callback(blob);
                } else {
                    next();
                }
            }, "image/jpeg", p.q);
        }

        next();
    }

    function initCropperWhenModalShown() {
        var cropImg = document.getElementById("recipeCropImage");
        if (!cropImg || !cropImg.src) return;

        if (cropper) {
            cropper.destroy();
            cropper = null;
        }

        if (typeof Cropper === "undefined") {
            console.error("Cropper.js not loaded");
            return;
        }

        cropper = new Cropper(cropImg, {
            aspectRatio: ASPECT,
            viewMode: 1,
            dragMode: "move",
            autoCropArea: 1,
            responsive: true,
            background: false
        });
    }

    function wire() {
        var inputFile = getInput();
        var cropImg = document.getElementById("recipeCropImage");
        var applyBtn = document.getElementById("recipeCropApply");
        var modal = document.getElementById("recipeCropModal");

        if (!inputFile || !cropImg || !applyBtn || !modal) return;

        if (typeof jQuery === "undefined") {
            console.error("jQuery required for Bootstrap modal");
            return;
        }

        var $modal = jQuery(modal);

        inputFile.addEventListener("change", function () {
            var file = this.files[0];
            cropApplied = false;
            if (!file) return;

            if (file.size > 12 * 1024 * 1024) {
                alert("Image is too large. Please choose a file under 12 MB.");
                inputFile.value = "";
                return;
            }

            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
                objectUrl = null;
            }
            objectUrl = URL.createObjectURL(file);
            cropImg.src = objectUrl;

            cropImg.onload = function () {
                $modal.modal("show");
            };
        });

        $modal.on("shown.bs.modal", function () {
            initCropperWhenModalShown();
        });

        applyBtn.addEventListener("click", function () {
            if (!cropper) return;

            exportUnderLimit(cropper, function (blob) {
                if (!blob) {
                    alert("Could not compress the image under 2 MB. Try a smaller source image.");
                    return;
                }

                cropApplied = true;
                assignFileToInput(blob);
                setPreviewFromBlob(blob);

                if (cropper) {
                    cropper.destroy();
                    cropper = null;
                }
                cropImg.src = "";
                if (objectUrl) {
                    URL.revokeObjectURL(objectUrl);
                    objectUrl = null;
                }
                $modal.modal("hide");
            });
        });

        $modal.on("hidden.bs.modal", function () {
            if (cropper) {
                cropper.destroy();
                cropper = null;
            }
            cropImg.src = "";
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
                objectUrl = null;
            }
            if (!cropApplied) {
                if (lastAcceptedBlob) {
                    assignFileToInput(lastAcceptedBlob);
                    setPreviewFromBlob(lastAcceptedBlob);
                } else {
                    inputFile.value = "";
                }
            }
            cropApplied = false;
        });
    }

    /** Call from "Remove image" buttons so a new upload session does not restore an old crop. */
    window.recipeImageCropClearAccepted = function () {
        lastAcceptedBlob = null;
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", wire);
    } else {
        wire();
    }
})();
