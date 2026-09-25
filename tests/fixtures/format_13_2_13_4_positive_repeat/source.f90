! rule: C1304
! covers: positive-repeat
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_positive_repeat
  implicit none
  integer :: checks
  character(len=2) :: buf
  checks = 0
  buf = '##'
  write(buf,'(SS,2I1)') 4,5
  if (len(buf) /= 2) then
    write(*,'(a)') 'F132134:positive_repeat:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '45') then
    write(*,'(a)') 'F132134:positive_repeat:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:positive_repeat:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 POSITIVE_REPEAT OK'
end program f132134_positive_repeat
