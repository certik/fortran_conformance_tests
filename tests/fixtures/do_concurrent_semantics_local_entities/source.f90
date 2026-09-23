! rule: S11.1.7.5-002
! covers: local-hides-outside-variable
! covers: local-nonpointer-same-bounds
program do_concurrent_semantics_local_entities
  implicit none
  integer :: checks
  integer :: i
  integer :: local_scalar
  integer :: local_array(2:5)
  integer :: result(2:5), lower_seen(2:5), upper_seen(2:5)
  checks = 0
  local_scalar = 17
  local_array = -444
  result = -901
  lower_seen = -902
  upper_seen = -903
  do concurrent (i = 2:2) local(local_scalar, local_array) shared(result, lower_seen, upper_seen)
    local_scalar = 100 + i
    local_array = -333
    local_array(i) = local_scalar
    result(i) = local_array(i)
    lower_seen(i) = lbound(local_array, 1)
    upper_seen(i) = ubound(local_array, 1)
  end do
  if (local_scalar /= 17) then
    write(*,'(a)') 'DCS:local_entities:outside-scalar'
    error stop
  end if
  checks = checks + 1
  if (any(local_array /= -444)) then
    write(*,'(a)') 'DCS:local_entities:outside-array'
    error stop
  end if
  checks = checks + 1
  if (result(2) /= 102) then
    write(*,'(a)') 'DCS:local_entities:local-value'
    error stop
  end if
  checks = checks + 1
  if (lower_seen(2) /= 2) then
    write(*,'(a)') 'DCS:local_entities:lower-bound'
    error stop
  end if
  checks = checks + 1
  if (upper_seen(2) /= 5) then
    write(*,'(a)') 'DCS:local_entities:upper-bound'
    error stop
  end if
  checks = checks + 1
  if (checks /= 5) then
    write(*,'(a)') 'DCS:local_entities:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS LOCAL ENTITIES OK'
end program do_concurrent_semantics_local_entities
