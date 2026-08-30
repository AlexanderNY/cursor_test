import outlineMarkdown from './interview-prep.md?raw'
import { countNodes, parseOutlineMarkdown, type MindNode } from './parse-outline'

export const learningMapMarkdown = outlineMarkdown

export const learningMapRoot: MindNode = parseOutlineMarkdown(outlineMarkdown)

export const learningMapStats = {
  nodes: countNodes(learningMapRoot),
  branches: learningMapRoot.children.length,
}
