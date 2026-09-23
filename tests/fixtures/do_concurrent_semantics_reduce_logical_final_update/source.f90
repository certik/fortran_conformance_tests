! rule: S11.1.7.5-008
! covers: reduce-final-logical-result
program do_concurrent_semantics_reduce_logical_final_update
  implicit none
  integer :: checks
  integer :: i
  logical :: and_final, or_final
  logical :: eqv_final, neqv_final
  checks = 0
  and_final = .true.
  or_final = .false.
  eqv_final = .true.
  neqv_final = .true.
  do concurrent (i = 1:3) reduce(.and.:and_final) reduce(.or.:or_final) &
      reduce(.eqv.:eqv_final) reduce(.neqv.:neqv_final)
    and_final = and_final .and. (i /= 2)
    or_final = or_final .or. (i == 2)
    eqv_final = eqv_final .eqv. (i /= 2)
    neqv_final = neqv_final .neqv. (i == 1)
  end do
  if (and_final) then
    write(*,'(a)') 'DCS:reduce_logical_final_update:and-final'
    error stop
  end if
  checks = checks + 1
  if (.not. or_final) then
    write(*,'(a)') 'DCS:reduce_logical_final_update:or-final'
    error stop
  end if
  checks = checks + 1
  if (eqv_final) then
    write(*,'(a)') 'DCS:reduce_logical_final_update:eqv-final'
    error stop
  end if
  checks = checks + 1
  if (neqv_final) then
    write(*,'(a)') 'DCS:reduce_logical_final_update:neqv-final'
    error stop
  end if
  checks = checks + 1
  if (checks /= 4) then
    write(*,'(a)') 'DCS:reduce_logical_final_update:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS REDUCE LOGICAL FINAL UPDATE OK'
end program do_concurrent_semantics_reduce_logical_final_update
