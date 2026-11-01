import { BotsSettingsSection } from './bots-settings-section'
import { usePollsContext } from './polls-context'

export function PollsBotsPage() {
  const { selectedBotId, setSelectedBotId, handleBotsLoaded, loadModes } = usePollsContext()

  return (
    <BotsSettingsSection
      selectedBotId={selectedBotId}
      onSelectBot={setSelectedBotId}
      onBotsLoaded={handleBotsLoaded}
      onBotsChanged={() => loadModes(selectedBotId)}
    />
  )
}
