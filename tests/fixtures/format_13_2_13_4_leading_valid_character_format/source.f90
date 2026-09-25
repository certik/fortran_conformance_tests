! rule: S13.2.2-001
! covers: leading-valid-format
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_leading_valid_character_format
  implicit none
  integer :: checks
  character(len=10) :: fmt
  character(len=3) :: buf
  checks = 0
  fmt = '(SS,I3)XYZ'
  buf = '###'
  write(buf,fmt) 7
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:leading_valid_character_format:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '  7') then
    write(*,'(a)') 'F132134:leading_valid_character_format:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:leading_valid_character_format:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 LEADING_VALID_CHARACTER_FORMAT OK'
end program f132134_leading_valid_character_format
