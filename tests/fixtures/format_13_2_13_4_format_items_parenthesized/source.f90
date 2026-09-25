! rule: R1302
! covers: format-items-parenthesized
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_format_items_parenthesized
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'(SS,I3)') 7
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:format_items_parenthesized:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '  7') then
    write(*,'(a)') 'F132134:format_items_parenthesized:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:format_items_parenthesized:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 FORMAT_ITEMS_PARENTHESIZED OK'
end program f132134_format_items_parenthesized
