import io, os, sys

ROOT = "."

def patch(path, edits):
    p = os.path.join(ROOT, path)
    s = io.open(p, encoding="utf-8").read()
    for name, old, new in edits:
        n = s.count(old)
        if n != 1:
            print("FAIL %s %s count=%d" % (path, name, n))
            sys.exit(1)
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8").write(s)
    print("PATCHED %s (%d)" % (path, len(edits)))

STORE = [
("append-sig", r'''export async function appendMascotMessage({
    text,
    images = [],
}: {
    text: string;
    images?: string[];
}): Promise<boolean> {''', r'''export async function appendMascotMessage({
    text,
    images = [],
    displayText,
}: {
    text: string;
    images?: string[];
    /** 只影响 UI 显示，不影响发给模型的 text —— 给「文件卡」这类
     *  「正文很长但气泡只该显示一行摘要」的场景用。 */
    displayText?: string;
}): Promise<boolean> {'''),

("append-userMsg", r'''    const userMsg: MascotMsg = images.length > 0
        ? { role: "user", text: trimmed, images, createdAt: new Date().toISOString() }
        : { role: "user", text: trimmed, createdAt: new Date().toISOString() };''', r'''    const shown = typeof displayText === "string" ? displayText.trim() : "";
    const userMsg: MascotMsg = images.length > 0
        ? { role: "user", text: trimmed, images, ...(shown ? { displayText: shown } : {}), createdAt: new Date().toISOString() }
        : { role: "user", text: trimmed, ...(shown ? { displayText: shown } : {}), createdAt: new Date().toISOString() };'''),

("append-title", r'''            ? { ...session, title: autoMascotSessionTitle(trimmed || "（图片）") }''', r'''            ? { ...session, title: autoMascotSessionTitle(shown || trimmed || "（图片）") }'''),

("send-sig", r'''export async function sendMascotMessage({
    text,
    images = [],
    context = getMascotContext(),
}: {
    text: string;
    images?: string[];
    context?: MascotPageContext;
}): Promise<void> {
    const accepted = await appendMascotMessage({ text, images });''', r'''export async function sendMascotMessage({
    text,
    images = [],
    displayText,
    context = getMascotContext(),
}: {
    text: string;
    images?: string[];
    /** 只影响 UI 显示的摘要（见 appendMascotMessage） */
    displayText?: string;
    context?: MascotPageContext;
}): Promise<void> {
    const accepted = await appendMascotMessage({ text, images, displayText });'''),
]

MASCOT = [
("lucide", '''AlertCircle, ChevronLeft, Code, Image as ImageIcon, MessageSquare, MoreHorizontal, RotateCcw, Sparkles, Trash2, UserRound } from "lucide-react";''', '''AlertCircle, ChevronLeft, Code, FileText, Image as ImageIcon, MessageSquare, MoreHorizontal, RotateCcw, Sparkles, Trash2, UserRound } from "lucide-react";'''),

("store-import", '''import {
    clearMascotToolHistoryMessages,''', '''import {
    appendMascotMessage,
    clearMascotToolHistoryMessages,'''),

("doc-import", '''} from "@/lib/mascot-chat-store";
import type { MascotMsg } from "@/lib/mascot-engine";''', '''} from "@/lib/mascot-chat-store";
import { ChatDocAttachmentTray, ChatDocImportSheet } from "./chat-doc-import";
import {
    attachmentCardLabel,
    resolveAttachmentText,
    type ChatDocAttachment,
} from "@/lib/chat-document-import";
import type { MascotMsg } from "@/lib/mascot-engine";'''),

("state", r'''    const [pendingImages, setPendingImages] = useState<string[]>([]);''', r'''    const [pendingImages, setPendingImages] = useState<string[]>([]);
    // 文件导入：待发的长文档卡片（发送时全文进上下文，气泡只显示一行摘要）
    const [docAttachments, setDocAttachments] = useState<ChatDocAttachment[]>([]);
    const [docImportOpen, setDocImportOpen] = useState(false);'''),

("handleSend", r'''        const text = inputText.trim();
        if (!text && pendingImages.length === 0) return;
        setInputText("");
        textareaRef.current?.style.setProperty("height", "auto");
        const images = pendingImages;
        setPendingImages([]);
        setShowEmojiPanel(false);
        await sendMascotMessage({ text, images, context });
    };''', r'''        const text = inputText.trim();
        const docs = docAttachments;
        if (!text && pendingImages.length === 0 && docs.length === 0) return;
        setInputText("");
        textareaRef.current?.style.setProperty("height", "auto");
        const images = pendingImages;
        setPendingImages([]);
        setDocAttachments([]);
        setShowEmojiPanel(false);
        // 文件卡：text 放全文（进模型上下文），displayText 放一行摘要（气泡只显示卡片）
        for (const attachment of docs) {
            const body = resolveAttachmentText(attachment);
            if (!body.trim()) continue;
            await appendMascotMessage({ text: body, displayText: attachmentCardLabel(attachment) });
        }
        if (text || images.length > 0) {
            await sendMascotMessage({ text, images, context });
        } else if (docs.length > 0) {
            // 只发文件没打字：材料进上下文后直接要一次回复
            await generateMascotReply({ context });
        }
    };'''),

("tray", '''                )}
                <textarea
                    ref={textareaRef}''', r'''                )}
                <ChatDocAttachmentTray
                    attachments={docAttachments}
                    onRemove={(docId) => setDocAttachments((prev) => prev.filter((item) => item.docId !== docId))}
                    onInsert={(attachment) => appendEmoji(resolveAttachmentText(attachment))}
                    onOpenImport={() => setDocImportOpen(true)}
                    disabled={chat.isThinking}
                />
                <textarea
                    ref={textareaRef}'''),

("send-btn", '''                    <button
                        type="button"
                        onClick={() => void handleSend()}
                        disabled={!chat.isThinking && !inputText.trim() && pendingImages.length === 0}''', r'''                    <button
                        type="button"
                        onClick={() => setDocImportOpen(true)}
                        className="ui-bare-btn text-[var(--c-text)]"
                        aria-label="导入文件"
                        title="导入文件（docx / doc / txt / md / pdf）"
                    >
                        <FileText size={22} strokeWidth={1.5} />
                    </button>
                    <button
                        type="button"
                        onClick={() => void handleSend()}
                        disabled={!chat.isThinking && !inputText.trim() && pendingImages.length === 0 && docAttachments.length === 0}'''),

("sheet", r'''                {showEmojiPanel && <EmojiPanel onSelect={appendEmoji} />}
            </div>''', r'''                {showEmojiPanel && <EmojiPanel onSelect={appendEmoji} />}
            </div>

            <ChatDocImportSheet
                open={docImportOpen}
                onClose={() => setDocImportOpen(false)}
                onInsertText={(text) => appendEmoji(text)}
                onAttach={(attachment) => setDocAttachments((prev) => (
                    prev.some((item) => item.docId === attachment.docId)
                        ? prev.map((item) => (item.docId === attachment.docId ? attachment : item))
                        : [...prev, attachment]
                ))}
            />'''),
]

ROOM = [
("import", r'''import { EmojiPanel, StickerPanel } from "./emoji-panel";''', r'''import { EmojiPanel, StickerPanel } from "./emoji-panel";
import { ChatDocAttachmentTray, ChatDocImportSheet } from "./chat-doc-import";
import {
    attachmentCardLabel,
    resolveAttachmentText,
    type ChatDocAttachment,
} from "@/lib/chat-document-import";'''),

("lucide", '''Clapperboard, Clock, Gift,''', '''Clapperboard, Clock, FileText, Gift,'''),

("props-type", '''onSendSticker: (name: string, url?: string) => void;
}>''', r'''onSendSticker: (name: string, url?: string) => void;
    /** 待发的文件卡（导入的长文档） */
    docAttachments: ChatDocAttachment[];
    onRemoveDocAttachment: (docId: string) => void;
    onInsertDocAttachment: (attachment: ChatDocAttachment) => void;
    onOpenDocImport: () => void;
    /** 把待发文件卡落成消息；返回 false = 被拒（如禁言中） */
    onSendDocAttachments: () => boolean;
}>'''),

("destructure", '''    onSendSticker,
}, ref) {''', '''    onSendSticker,
    docAttachments,
    onRemoveDocAttachment,
    onInsertDocAttachment,
    onOpenDocImport,
    onSendDocAttachments,
}, ref) {'''),

("submit", r'''        const trimmed = inputText.trim();
        if (!trimmed) return;
        if (!onSendText(trimmed)) return;''', r'''        const trimmed = inputText.trim();
        const hasDocs = docAttachments.length > 0;
        // 只有附件、没有文字也算一次有效发送（把材料丢给角色读）
        if (!trimmed && !hasDocs) return;
        if (hasDocs && !onSendDocAttachments()) return;
        if (trimmed && !onSendText(trimmed, { autoReply: false })) return;
        // 有附件时顺手要一次回复（材料刚进上下文，角色该有反应）；
        // 纯文字保持原样——发送本身不自动触发回复，由「主动回复」按钮决定
        if (hasDocs) onTriggerAIResponse();'''),

("plus-item", '''label: "语音条", onClick: () => onOpenRichModal("voice_msg") },''', r'''label: "语音条", onClick: () => onOpenRichModal("voice_msg") },
        { icon: <FileText size={22} strokeWidth={1.5} color="var(--c-text)" />, label: "导入文件", onClick: onOpenDocImport },'''),

("tray", '''            {suggestEnabled && (
                <StickerSearchSuggest''', r'''            <ChatDocAttachmentTray
                attachments={docAttachments}
                onRemove={onRemoveDocAttachment}
                onInsert={onInsertDocAttachment}
                onOpenImport={onOpenDocImport}
                disabled={inputLocked}
            />

            {suggestEnabled && (
                <StickerSearchSuggest'''),

("send-btn", r'''                <button
                    onClick={handleSubmit}
                    disabled={!isGenerating && (inputLocked || !inputText.trim())}''', r'''                <button
                    onClick={onOpenDocImport}
                    disabled={inputLocked}
                    className="ui-bare-btn text-[var(--c-text)]"
                    style={inputLocked ? { opacity: 0.35 } : undefined}
                    aria-label="导入文件"
                    title="导入文件（docx / doc / txt / md / pdf）到对话"
                >
                    <FileText size={22} strokeWidth={1.5} />
                </button>
                <button
                    onClick={handleSubmit}
                    disabled={!isGenerating && (inputLocked || (!inputText.trim() && docAttachments.length === 0))}'''),

("state", '''    const offlineTextInputRef = useRef<OfflineTextInputHandle | null>(null);''', r'''    const offlineTextInputRef = useRef<OfflineTextInputHandle | null>(null);
    // 文件导入：待发的长文档卡片（发送时正文进上下文，气泡只显示一张卡）
    const [docAttachments, setDocAttachments] = useState<ChatDocAttachment[]>([]);
    const [docImportOpen, setDocImportOpen] = useState(false);'''),

("funcs", '''    // 线下 XML 构造与提示词查看器共用 lib/offline-prompt-builder（社区 #108），''', r'''    // ── 文件导入 ──────────────────────────────────────────
    // 把待发文件卡落成消息：正文（含分类/标签/备注头 + 所选章节）写进 media_file 消息的
    // content —— llm-prompt-assembler 对 media_file 取 msg.content，所以角色拿得到全文；
    // 气泡只渲染一张文件卡，不在聊天里刷一整面墙。
    const sendDocAttachments = (): boolean => {
        if (!ensureGroupSpeakPermission()) return false;
        if (!docAttachments.length) return false;
        cancelFollowUp(session.id);
        const committed: ChatMessage[] = [];
        for (const attachment of docAttachments) {
            const text = resolveAttachmentText(attachment);
            if (!text.trim()) continue;
            committed.push(pushChatMessage({
                sessionId: session.id,
                role: "user",
                content: text,
                mediaType: "media_file",
                mediaData: {
                    fileType: "file",
                    fileName: attachmentCardLabel(attachment),
                    label: attachment.title,
                },
            }));
        }
        if (!committed.length) {
            setDocAttachments([]);
            return false;
        }
        setMessages(prev => [...prev, ...committed]);
        setDocAttachments([]);
        setPendingGenerate(true);
        return true;
    };

    const insertDocAttachmentText = (attachment: ChatDocAttachment) => {
        chatTextInputRef.current?.appendText(resolveAttachmentText(attachment));
    };

    const removeDocAttachment = (docId: string) => {
        setDocAttachments(prev => prev.filter(item => item.docId !== docId));
    };

    // 线下 XML 构造与提示词查看器共用 lib/offline-prompt-builder（社区 #108），'''),

("props-pass", '''                onSendSticker={(name, url) => { setShowStickerPanel(false); sendRichMessage("sticker", { label: name, stickerUrl: url }); }}''', '''                onSendSticker={(name, url) => { setShowStickerPanel(false); sendRichMessage("sticker", { label: name, stickerUrl: url }); }}
                docAttachments={docAttachments}
                onRemoveDocAttachment={removeDocAttachment}
                onInsertDocAttachment={insertDocAttachmentText}
                onOpenDocImport={() => { setShowEmojiPanel(false); setShowStickerPanel(false); setShowPlusMenu(false); setDocImportOpen(true); }}
                onSendDocAttachments={sendDocAttachments}'''),

("sheet", '''            {showConfirmMultiDelete && (''', r'''            <ChatDocImportSheet
                open={docImportOpen}
                onClose={() => setDocImportOpen(false)}
                onInsertText={(text) => chatTextInputRef.current?.appendText(text)}
                onAttach={(attachment) => setDocAttachments(prev => (
                    prev.some(item => item.docId === attachment.docId)
                        ? prev.map(item => (item.docId === attachment.docId ? attachment : item))
                        : [...prev, attachment]
                ))}
                onNotice={(message) => showChatToast(message)}
            />

            {showConfirmMultiDelete && ('''),
]

patch("lib/mascot-chat-store.ts", STORE)
patch("components/chat/mascot-chat-room.tsx", MASCOT)
patch("components/chat/chat-room.tsx", ROOM)
print("ALL_OK")
