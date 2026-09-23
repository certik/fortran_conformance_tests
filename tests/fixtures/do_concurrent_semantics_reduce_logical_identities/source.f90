! rule: S11.1.7.5-006
! covers: reduce-logical-initial-identities
program do_concurrent_semantics_reduce_logical_identities
  implicit none
  integer :: checks
  integer :: i
  logical :: and_identity, or_identity
  logical :: eqv_identity, neqv_identity
  logical :: contribution_guard
  checks = 0
  and_identity = .true.
  or_identity = .false.
  eqv_identity = .true.
  neqv_identity = .true.
  contribution_guard = .false.
  do concurrent (i = 1:3) reduce(.and.:and_identity) reduce(.or.:or_identity) &
      reduce(.eqv.:eqv_identity) reduce(.neqv.:neqv_identity) reduce(.or.:contribution_guard)
    and_identity = and_identity .and. .true.
    or_identity = or_identity .or. .false.
    eqv_identity = eqv_identity .eqv. .true.
    neqv_identity = neqv_identity .neqv. .false.
    contribution_guard = contribution_guard .or. (i == 2)
  end do
  if (.not. and_identity) then
    write(*,'(a)') 'DCS:reduce_logical_identities:and-identity'
    error stop
  end if
  checks = checks + 1
  if (or_identity) then
    write(*,'(a)') 'DCS:reduce_logical_identities:or-identity'
    error stop
  end if
  checks = checks + 1
  if (.not. eqv_identity) then
    write(*,'(a)') 'DCS:reduce_logical_identities:eqv-identity'
    error stop
  end if
  checks = checks + 1
  if (.not. neqv_identity) then
    write(*,'(a)') 'DCS:reduce_logical_identities:neqv-identity'
    error stop
  end if
  checks = checks + 1
  if (.not. contribution_guard) then
    write(*,'(a)') 'DCS:reduce_logical_identities:contribution-guard'
    error stop
  end if
  checks = checks + 1
  if (checks /= 5) then
    write(*,'(a)') 'DCS:reduce_logical_identities:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS REDUCE LOGICAL IDENTITIES OK'
end program do_concurrent_semantics_reduce_logical_identities
