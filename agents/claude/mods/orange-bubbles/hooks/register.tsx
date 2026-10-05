import type { Register } from 'claude-code'

// Very light orange, rgb(250, 214, 187).
const TINT = '#FED9BF'

export const register: Register = on => {
  on('ui.render', { component: 'AssistantMessage' }, async ($, e, next) => {
    const drawing = await next(e)
    if (!drawing) {
      return drawing
    }

    const { Box } = $.ui.resolve(e)

    return (
      <Box backgroundColor={TINT} paddingX={2} paddingY={2}>
        {drawing}
      </Box>
    )
  })
}
