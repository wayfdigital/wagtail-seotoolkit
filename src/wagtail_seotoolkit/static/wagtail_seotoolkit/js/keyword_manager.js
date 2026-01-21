/**
 * Keyword Manager
 *
 * Handles target keyword management in the page editor sidepanel.
 * Displays keywords as bubbles/chips with delete buttons.
 * Auto-saves when keywords are added or removed.
 */

(function () {
    "use strict";

    /**
     * Get CSRF token from Django
     */
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split("; ")
            .find((row) => row.startsWith("csrftoken="));

        if (cookieValue) {
            return cookieValue.split("=")[1];
        }

        const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
        if (csrfInput) {
            return csrfInput.value;
        }

        return null;
    }

    /**
     * Save keywords for a page
     */
    async function saveKeywords(pageId, keywords) {
        try {
            const formData = new FormData();
            formData.append("keywords", keywords.join(", "));

            const response = await fetch(`/admin/api/keywords/${pageId}/save/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                },
                body: formData,
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error("Failed to save keywords:", error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Show feedback message
     */
    function showFeedback(widget, message, isSuccess, duration = 2500) {
        const feedback = widget.querySelector(".seo-keyword-feedback");
        if (feedback) {
            feedback.textContent = message;
            feedback.className = `seo-keyword-feedback ${isSuccess ? "seo-keyword-feedback--success" : "seo-keyword-feedback--error"
                }`;
            feedback.style.display = "block";

            if (duration > 0) {
                setTimeout(() => {
                    feedback.style.display = "none";
                }, duration);
            }
        }
    }

    /**
     * Create a keyword bubble element
     */
    function createBubble(keyword, onRemove) {
        const bubble = document.createElement("span");
        bubble.className = "seo-keyword-bubble";
        bubble.dataset.keyword = keyword;

        const text = document.createElement("span");
        text.className = "seo-keyword-bubble__text";
        text.textContent = keyword;

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "seo-keyword-bubble__remove";
        removeBtn.title = "Remove keyword";
        removeBtn.innerHTML =
            '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>';
        removeBtn.addEventListener("click", (e) => {
            e.preventDefault();
            onRemove(keyword);
        });

        bubble.appendChild(text);
        bubble.appendChild(removeBtn);

        return bubble;
    }

    /**
     * Initialize keyword manager for a widget
     */
    function initKeywordWidget(widget) {
        // Prevent duplicate initialization
        if (widget.dataset.initialized === "true") {
            return;
        }

        const bubblesContainer = widget.querySelector(".seo-keyword-bubbles");
        const input = widget.querySelector(".seo-keyword-input");
        const addBtn = widget.querySelector(".seo-keyword-add");
        const pageId = widget.dataset.pageId;

        if (!bubblesContainer || !input || !addBtn || !pageId) {
            return;
        }

        // Mark as initialized
        widget.dataset.initialized = "true";

        // Current keywords state
        let keywords = [];

        // Parse initial keywords from data attribute
        const initialKeywords = widget.dataset.keywords || "";
        if (initialKeywords.trim()) {
            keywords = initialKeywords
                .split(",")
                .map((k) => k.trim())
                .filter((k) => k.length > 0);
        }

        /**
         * Render all keyword bubbles
         */
        function renderBubbles() {
            bubblesContainer.innerHTML = "";
            keywords.forEach((keyword) => {
                const bubble = createBubble(keyword, removeKeyword);
                bubblesContainer.appendChild(bubble);
            });
        }

        /**
         * Add a new keyword
         */
        async function addKeyword(keyword) {
            keyword = keyword.trim();
            if (!keyword) return;

            // Check for duplicates (case-insensitive)
            const keywordLower = keyword.toLowerCase();
            const isDuplicate = keywords.some((k) => k.toLowerCase() === keywordLower);

            if (isDuplicate) {
                showFeedback(widget, `"${keyword}" already exists`, false);
                return;
            }

            // Add to state
            keywords.push(keyword);
            renderBubbles();
            input.value = "";

            // Save to server
            widget.classList.add("seo-keyword-widget--saving");
            const result = await saveKeywords(pageId, keywords);
            widget.classList.remove("seo-keyword-widget--saving");

            if (result.success) {
                // Update with server-normalized keywords
                if (result.keywords) {
                    keywords = result.keywords
                        .split(",")
                        .map((k) => k.trim())
                        .filter((k) => k.length > 0);
                    renderBubbles();
                }
                showFeedback(widget, "Keyword added", true);
            } else {
                // Rollback on error
                keywords = keywords.filter((k) => k !== keyword);
                renderBubbles();
                showFeedback(widget, result.error || "Failed to add keyword", false);
            }
        }

        /**
         * Remove a keyword
         */
        async function removeKeyword(keyword) {
            // Remove from state
            const originalKeywords = [...keywords];
            keywords = keywords.filter((k) => k !== keyword);
            renderBubbles();

            // Save to server
            widget.classList.add("seo-keyword-widget--saving");
            const result = await saveKeywords(pageId, keywords);
            widget.classList.remove("seo-keyword-widget--saving");

            if (result.success) {
                showFeedback(widget, "Keyword removed", true);
            } else {
                // Rollback on error
                keywords = originalKeywords;
                renderBubbles();
                showFeedback(widget, result.error || "Failed to remove keyword", false);
            }
        }

        /**
         * Add keywords from input (supports comma-separated)
         */
        function addKeywordsFromInput() {
            const inputValue = input.value.trim();
            if (!inputValue) return;

            // Support comma-separated input
            const newKeywords = inputValue
                .split(",")
                .map((k) => k.trim())
                .filter((k) => k.length > 0);

            if (newKeywords.length === 1) {
                addKeyword(newKeywords[0]);
            } else if (newKeywords.length > 1) {
                // Add multiple keywords at once
                addMultipleKeywords(newKeywords);
            }
        }

        /**
         * Add multiple keywords at once
         */
        async function addMultipleKeywords(newKeywords) {
            // Filter out duplicates (case-insensitive)
            const existingLower = new Set(keywords.map((k) => k.toLowerCase()));
            const uniqueNew = [];
            const seenLower = new Set();

            for (const kw of newKeywords) {
                const kwLower = kw.toLowerCase();
                if (!existingLower.has(kwLower) && !seenLower.has(kwLower)) {
                    seenLower.add(kwLower);
                    uniqueNew.push(kw);
                }
            }

            if (uniqueNew.length === 0) {
                showFeedback(widget, "All keywords already exist", false);
                input.value = "";
                return;
            }

            // Add to state
            keywords = [...keywords, ...uniqueNew];
            renderBubbles();
            input.value = "";

            // Save to server
            widget.classList.add("seo-keyword-widget--saving");
            const result = await saveKeywords(pageId, keywords);
            widget.classList.remove("seo-keyword-widget--saving");

            if (result.success) {
                // Update with server-normalized keywords
                if (result.keywords) {
                    keywords = result.keywords
                        .split(",")
                        .map((k) => k.trim())
                        .filter((k) => k.length > 0);
                    renderBubbles();
                }
                const msg =
                    uniqueNew.length === 1
                        ? "Keyword added"
                        : `${uniqueNew.length} keywords added`;
                showFeedback(widget, msg, true);
            } else {
                // Rollback
                keywords = keywords.filter((k) => !uniqueNew.includes(k));
                renderBubbles();
                showFeedback(widget, result.error || "Failed to add keywords", false);
            }
        }

        // Event listeners
        addBtn.addEventListener("click", (e) => {
            e.preventDefault();
            addKeywordsFromInput();
        });

        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                addKeywordsFromInput();
            }
        });

        // Initial render
        renderBubbles();
    }

    /**
     * Initialize all keyword widgets on the page
     */
    function initAllKeywordWidgets() {
        const widgets = document.querySelectorAll(".seo-keyword-widget");
        widgets.forEach(initKeywordWidget);
    }

    /**
     * Initialize on page load
     */
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAllKeywordWidgets);
    } else {
        initAllKeywordWidgets();
    }

    // Re-initialize on Wagtail panel updates
    document.addEventListener("wagtail:panel-init", initAllKeywordWidgets);
})();
