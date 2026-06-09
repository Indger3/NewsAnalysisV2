import { Box, TextField, Button, Typography, CircularProgress } from '@mui/material'
import { wordCount } from '../utils/text'
//import AnalysisSettings from './AnalysisSettings'

// export default function ArticlePanel({ text, onChange, onSubmit, isAnalyzing, settings, onSettingsChange }) 
export default function ArticlePanel({
  text,
  onChange,
  onSubmit,
  isAnalyzing,

  batchFile,
  onBatchFileSelect,
  onBatchAnalyze
}){
  const words = wordCount(text)

  return (
    <Box sx={{
      width: '40%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      bgcolor: 'background.paper',
      borderRight: '1px solid',
      borderColor: 'divider',
      flexShrink: 0,
    }}>
      <Box sx={{
        px: 3,
        py: 2,
        borderBottom: '1px solid',
        borderColor: 'divider',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <Typography sx={{
          fontSize: '0.65rem',
          fontWeight: 800,
          letterSpacing: 1.8,
          textTransform: 'uppercase',
          color: 'text.secondary',
        }}>
          Article
        </Typography>
        {text && (
          <Typography variant="caption" color="text.disabled">
            {words.toLocaleString()} {words === 1 ? 'word' : 'words'}
          </Typography>
        )}
      </Box>

      <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex' }}>
        <TextField
          multiline
          fullWidth
          placeholder="Paste your news article here…"
          value={text}
          onChange={(e) => onChange(e.target.value)}
          sx={{
            flexGrow: 1,
            '& .MuiOutlinedInput-root': {
              height: '100%',
              alignItems: 'flex-start',
              borderRadius: 0,
              fontSize: '0.875rem',
              lineHeight: 1.75,
              color: 'text.primary',
              '& fieldset': { border: 'none' },
            },
            '& .MuiOutlinedInput-input': {
              height: '100% !important',
              overflowY: 'auto !important',
              p: '20px 24px',
              resize: 'none',
            },
            '& .MuiInputBase-inputMultiline': {
              height: '100% !important',
            },
          }}
        />
      </Box>

      {/* <AnalysisSettings settings={settings} onChange={onSettingsChange} /> */}
<Box
  sx={{
    p: 2,
    borderTop: '1px solid',
    borderBottom: '1px solid',
    borderColor: 'divider',
  }}
>
  <Typography
    sx={{
      fontSize: '0.75rem',
      fontWeight: 700,
      mb: 1,
    }}
  >
    Batch Analysis
  </Typography>

  <Button
    component="label"
    variant="outlined"
    fullWidth
  >
    Upload JSON File

    <input
      hidden
      type="file"
      accept=".json"
      onChange={(e) => onBatchFileSelect(e.target.files?.[0])}
    />
  </Button>

  {batchFile && (
    <Typography
      variant="caption"
      sx={{
        display: 'block',
        mt: 1,
      }}
    >
      {batchFile.name}
    </Typography>
  )}

  <Button
    variant="contained"
    fullWidth
    sx={{ mt: 2 }}
    disabled={!batchFile}
    onClick={onBatchAnalyze}
  >
    Analyze Batch File
  </Button>
</Box>
      <Box sx={{
        px: 3,
        py: 2.5,
        borderTop: '1px solid',
        borderColor: 'divider',
        bgcolor: '#fafbfc',
      }}>
        <Button
          variant="contained"
          size="large"
          fullWidth
          disabled={!text.trim() || isAnalyzing}
          onClick={onSubmit}
          startIcon={isAnalyzing ? <CircularProgress size={16} color="inherit" /> : null}
          sx={{ py: 1.5 }}
        >
          {isAnalyzing ? 'Analyzing…' : 'Analyze Article'}
        </Button>
      </Box>
    </Box>
  )
}
