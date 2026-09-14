! rule: S6.2.1-001
! covers: character-literal
! evidence: positive-control
! Punctuation inside this literal does not claim delimiter-token facets.
program token_character_admission
    implicit none
    character(len=6) :: value

    value = '(/[]/)'
    if (value /= '(/[]/)') error stop 1
end program token_character_admission
