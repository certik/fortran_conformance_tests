! rule: S13.4-004
! covers: repeated-parenthesized-group
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_repeated_parenthesized_group
  implicit none
  integer :: checks
  character(len=4) :: buf
  checks = 0
  buf = '####'
  write(buf,'(SS,2(I1,","))') 6,7
  if (len(buf) /= 4) then
    write(*,'(a)') 'F132134:repeated_parenthesized_group:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '6,7,') then
    write(*,'(a)') 'F132134:repeated_parenthesized_group:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:repeated_parenthesized_group:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 REPEATED_PARENTHESIZED_GROUP OK'
end program f132134_repeated_parenthesized_group
