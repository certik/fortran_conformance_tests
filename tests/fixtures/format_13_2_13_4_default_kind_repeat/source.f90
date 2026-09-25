! rule: C1305
! covers: default-kind-repeat
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_default_kind_repeat
  implicit none
  integer :: checks
  character(len=3) :: buf
  checks = 0
  buf = '###'
  write(buf,'(SS,3I1)') 4,5,6
  if (len(buf) /= 3) then
    write(*,'(a)') 'F132134:default_kind_repeat:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (buf /= '456') then
    write(*,'(a)') 'F132134:default_kind_repeat:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:default_kind_repeat:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 DEFAULT_KIND_REPEAT OK'
end program f132134_default_kind_repeat
