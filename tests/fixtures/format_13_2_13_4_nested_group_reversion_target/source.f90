! rule: S13.4-009
! covers: nested-group-reversion-target
! Expected bytes are hand-derived from Fortran 2023 clauses 13.2-13.4.
program f132134_nested_group_reversion_target
  implicit none
  integer :: checks
  character(len=3) :: rec(3)
  character(len=9) :: observed
  checks = 0
  rec = '#'
  observed = '#########'
  write(rec,'(SS,"H",(I1,","))') 1,2,3
  observed = rec(1) // rec(2) // rec(3)
  if (len(observed) /= 9) then
    write(*,'(a)') 'F132134:nested_group_reversion_target:observed-length'
    error stop 1
  end if
  checks = checks + 1
  if (observed /= 'H1,2, 3, ') then
    write(*,'(a)') 'F132134:nested_group_reversion_target:observed-characters'
    error stop 1
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'F132134:nested_group_reversion_target:check-total'
    error stop 1
  end if
  write(*,'(a)') 'FORMAT 13.2-13.4 NESTED_GROUP_REVERSION_TARGET OK'
end program f132134_nested_group_reversion_target
