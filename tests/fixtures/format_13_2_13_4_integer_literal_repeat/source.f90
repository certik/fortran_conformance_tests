! rule: R1306
! covers: integer-literal-repeat
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_integer_literal_repeat
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'(SS,3I1)') 1,2,3
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:integer_literal_repeat:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '123') then
    write(*,'(a)') 'F132134:integer_literal_repeat:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:integer_literal_repeat:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 INTEGER_LITERAL_REPEAT OK'
end program f132134_integer_literal_repeat
