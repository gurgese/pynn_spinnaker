#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/log.h"

//-----------------------------------------------------------------------------
// SynapseProcessor::KeyLookupBinarySearch
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
template<unsigned int S>
class KeyLookupBinarySearch
{
public:
  KeyLookupBinarySearch() : m_LookupEntries(NULL), m_NumLookupEntries(NULL)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  bool LookupRow(uint32_t key, uint32_t *baseAddress, unsigned int &numSynapses, uint32_t *&popAddress) const
  {
    // Binary search lookup table
    unsigned int iMin = 0;
    unsigned int iMax = m_NumLookupEntries;
    while (iMin < iMax)
    {
      const unsigned int iMid = (iMax + iMin) / 2;
      const auto &lookupEntry = m_LookupEntries[iMid];
      if ((key & lookupEntry.m_Mask) == lookupEntry.m_Key)
      {
        // Extract number of synapses and word offset from lookup entry
        // **NOTE** add one as 0 is not a valid number
        numSynapses = (lookupEntry.m_WordOffsetRowSynapses & RowSynapsesMask) + 1;
        const uint32_t wordOffset = lookupEntry.m_WordOffsetRowSynapses >> S;

        // Add word offset to base address to get row address
        popAddress = baseAddress + wordOffset;

        LOG_PRINT(LOG_LEVEL_TRACE, "Spike key:%08x - Population address:%08x, Num synapses:%u",
                  key, popAddress, numSynapses);

        return true;
      }
      // Otherwise, entry must be in upper part of the table
      else if (lookupEntry.m_Key < key)
      {
        iMin = iMid + 1;
      }
      // Otherwise, entry must be in lower part of the table
      else
      {
        iMax = iMid;
      }
    }

    LOG_PRINT(LOG_LEVEL_WARN, "Population associated with spike key %08x not found in key lookup", key);
    return false;
  }

  bool ReadSDRAMData(uint32_t *baseAddress, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "ReadKeyLookupRegion");

    // Read base address and num lookup entries from 1st 2 words
    m_NumLookupEntries = baseAddress[0];
    LOG_PRINT(LOG_LEVEL_INFO, "\tNum lookup entries:%u", m_NumLookupEntries);

    // Allocate lookup entries
    const unsigned int lookupEntriesBytes = m_NumLookupEntries * sizeof(KeyLookupEntry);
    m_LookupEntries = (KeyLookupEntry*)spin1_malloc(lookupEntriesBytes);
    if(m_LookupEntries == NULL)
    {
      return false;
    }

    // Copy data into newly allocated array
    spin1_memcpy(m_LookupEntries, &baseAddress[1], lookupEntriesBytes);

#if LOG_LEVEL <= LOG_LEVEL_TRACE
  LOG_PRINT(LOG_LEVEL_TRACE, "\tPopulations");
  LOG_PRINT(LOG_LEVEL_TRACE, "\t------------------------------------------");
  for(unsigned int i = 0; i < m_NumLookupEntries; i++)
  {
    const auto &lookupEntry = m_LookupEntries[i];
    LOG_PRINT(LOG_LEVEL_TRACE, "\t\tKey:%08x, Mask:%08x, Num synapses:%u, Word offset:%u",
      lookupEntry.m_Key, lookupEntry.m_Mask,
      lookupEntry.m_WordOffsetRowSynapses & RowSynapsesMask,
      lookupEntry.m_WordOffsetRowSynapses >> S);
  }
  LOG_PRINT(LOG_LEVEL_TRACE, "\t------------------------------------------");
#endif

    return true;
  }

private:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t RowSynapsesMask = (1 << S) - 1;

  //-----------------------------------------------------------------------------
  // KeyLookupEntry
  //-----------------------------------------------------------------------------
  // **THINK** mask could be a byte index into an array of
  // masks as there are going to be very few mask format
  struct KeyLookupEntry
  {
    uint32_t m_Key;
    uint32_t m_Mask;
    uint32_t m_WordOffsetRowSynapses;
  };

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  KeyLookupEntry *m_LookupEntries;
  unsigned int m_NumLookupEntries;
};
}