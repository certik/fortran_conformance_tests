! rule: S13.2.1-001
! covers: character-string-blanks-preserved
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_character_string_blanks_preserved
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'("A B")')
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:character_string_blanks_preserved:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= 'A B') then
    write(*,'(a)') 'F132134:character_string_blanks_preserved:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:character_string_blanks_preserved:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 CHARACTER_STRING_BLANKS_PRESERVED OK'
end program f132134_character_string_blanks_preserved
