import type { Register } from 'claude-code'

// Very light orange, rgb(250, 214, 187).
const ASSISTANT_TINT = '#FED9BF'
// The same tint over a white page at half opacity, so a selection highlight
// the desktop draws behind the message can show through.
const ASSISTANT_TINT_SEE_THROUGH = '#FDB37F80'

export const register: Register = on => {
  on('ui.render', { component: 'AssistantMessage' }, async ($, e, next) => {
    const drawing = await next(e)
    if (!drawing) {
      return drawing
    }

    const { Box } = $.ui.resolve(e)

    if (e.surface === 'desktop') {
      return (
        <Box
          backgroundColor={ASSISTANT_TINT_SEE_THROUGH}
          borderStyle="round"
          borderColor={ASSISTANT_TINT}
          paddingX={2}
          paddingY={2}
        >
          {drawing}
        </Box>
      )
    }

    return (
      <Box backgroundColor={ASSISTANT_TINT} paddingX={2} paddingY={2}>
        {drawing}
      </Box>
    )
  })
}
