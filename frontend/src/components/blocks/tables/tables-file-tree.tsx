"use client";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
  ChevronDown,
  ChevronRight,
  File,
  FileCode,
  FileImage,
  FileText,
  Folder,
  FolderOpen,
  Music,
  Video,
} from "lucide-react";
import { useState } from "react";

interface FileNode {
  id: string;
  name: string;
  type: "folder" | "file";
  size?: string;
  modified: string;
  children?: FileNode[];
  fileType?: "document" | "image" | "code" | "video" | "audio" | "other";
}

const fileTree: FileNode[] = [
  {
    id: "src",
    name: "src",
    type: "folder",
    modified: "Today",
    children: [
      {
        id: "src/components",
        name: "components",
        type: "folder",
        modified: "Today",
        children: [
          { id: "src/components/Button.tsx", name: "Button.tsx", type: "file", size: "2.4 KB", modified: "2 hours ago", fileType: "code" },
          { id: "src/components/Card.tsx", name: "Card.tsx", type: "file", size: "1.8 KB", modified: "Yesterday", fileType: "code" },
          { id: "src/components/Input.tsx", name: "Input.tsx", type: "file", size: "3.1 KB", modified: "3 days ago", fileType: "code" },
        ],
      },
      {
        id: "src/pages",
        name: "pages",
        type: "folder",
        modified: "Yesterday",
        children: [
          { id: "src/pages/index.tsx", name: "index.tsx", type: "file", size: "1.2 KB", modified: "Today", fileType: "code" },
          { id: "src/pages/about.tsx", name: "about.tsx", type: "file", size: "890 B", modified: "1 week ago", fileType: "code" },
        ],
      },
      { id: "src/App.tsx", name: "App.tsx", type: "file", size: "2.1 KB", modified: "Today", fileType: "code" },
      { id: "src/index.css", name: "index.css", type: "file", size: "4.5 KB", modified: "3 days ago", fileType: "code" },
    ],
  },
  {
    id: "public",
    name: "public",
    type: "folder",
    modified: "1 week ago",
    children: [
      {
        id: "public/images",
        name: "images",
        type: "folder",
        modified: "1 week ago",
        children: [
          { id: "public/images/logo.png", name: "logo.png", type: "file", size: "24 KB", modified: "1 month ago", fileType: "image" },
          { id: "public/images/hero.jpg", name: "hero.jpg", type: "file", size: "156 KB", modified: "2 weeks ago", fileType: "image" },
        ],
      },
      { id: "public/favicon.ico", name: "favicon.ico", type: "file", size: "4 KB", modified: "2 months ago", fileType: "image" },
    ],
  },
  {
    id: "docs",
    name: "docs",
    type: "folder",
    modified: "3 days ago",
    children: [
      { id: "docs/README.md", name: "README.md", type: "file", size: "3.2 KB", modified: "3 days ago", fileType: "document" },
      { id: "docs/CHANGELOG.md", name: "CHANGELOG.md", type: "file", size: "8.7 KB", modified: "1 week ago", fileType: "document" },
    ],
  },
  { id: "package.json", name: "package.json", type: "file", size: "1.4 KB", modified: "Today", fileType: "code" },
  { id: "tsconfig.json", name: "tsconfig.json", type: "file", size: "682 B", modified: "1 month ago", fileType: "code" },
  { id: ".gitignore", name: ".gitignore", type: "file", size: "312 B", modified: "2 months ago", fileType: "other" },
];

function getFileIcon(node: FileNode) {
  if (node.type === "folder") {
    return null; // Handled separately with open/closed state
  }

  switch (node.fileType) {
    case "document":
      return <FileText className="h-4 w-4 text-blue-500" />;
    case "image":
      return <FileImage className="h-4 w-4 text-green-500" />;
    case "code":
      return <FileCode className="h-4 w-4 text-orange-500" />;
    case "video":
      return <Video className="h-4 w-4 text-purple-500" />;
    case "audio":
      return <Music className="h-4 w-4 text-pink-500" />;
    default:
      return <File className="h-4 w-4 text-muted-foreground" />;
  }
}

function FileTreeRow({
  node,
  depth,
  expanded,
  onToggle,
  selected,
  onSelect,
}: {
  node: FileNode;
  depth: number;
  expanded: Set<string>;
  onToggle: (id: string) => void;
  selected: Set<string>;
  onSelect: (id: string) => void;
}) {
  const isExpanded = expanded.has(node.id);
  const isSelected = selected.has(node.id);
  const hasChildren = node.type === "folder" && node.children && node.children.length > 0;

  return (
    <>
      <TableRow className={cn(isSelected && "bg-primary/5")}>
        <TableCell className="w-8">
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onSelect(node.id)}
          />
        </TableCell>
        <TableCell>
          <div
            className="flex items-center gap-1"
            style={{ paddingLeft: `${depth * 20}px` }}
          >
            {node.type === "folder" ? (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => onToggle(node.id)}
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            ) : (
              <span className="w-6" />
            )}
            {node.type === "folder" ? (
              isExpanded ? (
                <FolderOpen className="h-4 w-4 text-yellow-500" />
              ) : (
                <Folder className="h-4 w-4 text-yellow-500" />
              )
            ) : (
              getFileIcon(node)
            )}
            <span className={cn("ml-1.5", node.type === "folder" && "font-medium")}>
              {node.name}
            </span>
          </div>
        </TableCell>
        <TableCell className="text-right text-sm text-muted-foreground tabular-nums">
          {node.size || "--"}
        </TableCell>
        <TableCell className="text-sm text-muted-foreground">
          {node.modified}
        </TableCell>
      </TableRow>
      {isExpanded && hasChildren && node.children!.map((child) => (
        <FileTreeRow
          key={child.id}
          node={child}
          depth={depth + 1}
          expanded={expanded}
          onToggle={onToggle}
          selected={selected}
          onSelect={onSelect}
        />
      ))}
    </>
  );
}

export const title = "React Table Block File Tree";

export default function TableFileTree01() {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(["src", "src/components"]));
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const countItems = (nodes: FileNode[]): { folders: number; files: number } => {
    let folders = 0;
    let files = 0;
    for (const node of nodes) {
      if (node.type === "folder") {
        folders++;
        if (node.children) {
          const sub = countItems(node.children);
          folders += sub.folders;
          files += sub.files;
        }
      } else {
        files++;
      }
    }
    return { folders, files };
  };

  const { folders, files } = countItems(fileTree);

  return (
    <div style={{ width: "900px" }}>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Project Files</h3>
            <p className="text-sm text-muted-foreground">
              {folders} folders, {files} files
              {selected.size > 0 && ` - ${selected.size} selected`}
            </p>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
          <Table className="table-fixed" style={{ width: "850px" }}>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12" />
                <TableHead className="font-semibold text-foreground">Name</TableHead>
                <TableHead className="w-24 font-semibold text-foreground text-right">Size</TableHead>
                <TableHead className="w-32 font-semibold text-foreground">Modified</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fileTree.map((node) => (
                <FileTreeRow
                  key={node.id}
                  node={node}
                  depth={0}
                  expanded={expanded}
                  onToggle={toggleExpand}
                  selected={selected}
                  onSelect={toggleSelect}
                />
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="flex items-center gap-6 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <Folder className="h-3.5 w-3.5 text-yellow-500" />
            <span>Click chevron to expand</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileCode className="h-3.5 w-3.5 text-orange-500" />
            <span>Code files</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileImage className="h-3.5 w-3.5 text-green-500" />
            <span>Images</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-blue-500" />
            <span>Documents</span>
          </div>
        </div>
      </div>
    </div>
  );
}
