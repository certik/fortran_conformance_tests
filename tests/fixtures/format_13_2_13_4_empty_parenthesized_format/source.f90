! rule: R1302
! covers: empty-parenthesized-format
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_empty_parenthesized_format
  implicit none
  integer :: checks
  character(len=1) :: buf
  checks = 0
  buf = '#'
  write(buf,'()')
  if (len(buf) /= 1) then
    write(*,'(a)') 'F132134:empty_parenthesized_format:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= ' ') then
    write(*,'(a)') 'F132134:empty_parenthesized_format:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:empty_parenthesized_format:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 EMPTY_PARENTHESIZED_FORMAT OK'
end program f132134_empty_parenthesized_format
