! rule: S13.2.2-002
! covers: defined-through-final-parenthesis
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_defined_through_final_parenthesis
  implicit none
  integer :: checks
  character(len=7) :: fmt
  character(len=3) :: buf
  checks = 0
  fmt = '#######'
  fmt(1:7) = '(SS,I3)'
  buf = '###'
  write(buf,fmt) 7
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:defined_through_final_parenthesis:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '  7') then
    write(*,'(a)') 'F132134:defined_through_final_parenthesis:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:defined_through_final_parenthesis:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 DEFINED_THROUGH_FINAL_PARENTHESIS OK'
end program f132134_defined_through_final_parenthesis
