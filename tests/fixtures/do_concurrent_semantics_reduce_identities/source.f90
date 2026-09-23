! rule: S11.1.7.5-006
! covers: reduce-plus-initial-zero
! covers: reduce-times-initial-one
! covers: reduce-bitwise-initial-identities
! covers: reduce-minmax-initial-extremes
program do_concurrent_semantics_reduce_identities
  implicit none
  integer :: checks
  integer :: i
  integer :: sum_value, product_value
  integer :: or_value, and_value, xor_value
  integer :: max_value, min_value
  checks = 0
  sum_value = 50
  product_value = 3
  or_value = 16
  and_value = 255
  xor_value = 32
  max_value = -10
  min_value = 99
  do concurrent (i = 1:4) reduce(+:sum_value)
    sum_value = sum_value + i
  end do
  do concurrent (i = 1:4) reduce(*:product_value)
    product_value = product_value * 2
  end do
  do concurrent (i = 1:3) reduce(ior:or_value) reduce(iand:and_value) reduce(ieor:xor_value)
    or_value = ior(or_value, 2 * i + 1)
    and_value = iand(and_value, 255 - 2**i)
    xor_value = ieor(xor_value, 2 * i + 1)
  end do
  do concurrent (i = 1:4) reduce(max:max_value) reduce(min:min_value)
    max_value = max(max_value, i * 3)
    min_value = min(20 - i, min_value)
  end do
  if (sum_value /= 60) then
    write(*,'(a)') 'DCS:reduce_identities:plus'
    error stop
  end if
  checks = checks + 1
  if (product_value /= 48) then
    write(*,'(a)') 'DCS:reduce_identities:times'
    error stop
  end if
  checks = checks + 1
  if (or_value /= 23) then
    write(*,'(a)') 'DCS:reduce_identities:ior'
    error stop
  end if
  checks = checks + 1
  if (and_value /= 241) then
    write(*,'(a)') 'DCS:reduce_identities:iand'
    error stop
  end if
  checks = checks + 1
  if (xor_value /= 33) then
    write(*,'(a)') 'DCS:reduce_identities:ieor'
    error stop
  end if
  checks = checks + 1
  if (max_value /= 12) then
    write(*,'(a)') 'DCS:reduce_identities:max'
    error stop
  end if
  checks = checks + 1
  if (min_value /= 16) then
    write(*,'(a)') 'DCS:reduce_identities:min'
    error stop
  end if
  checks = checks + 1
  if (checks /= 7) then
    write(*,'(a)') 'DCS:reduce_identities:check-count'
    error stop
  end if
  write(*,'(a)') 'DO CONCURRENT SEMANTICS REDUCE IDENTITIES OK'
end program do_concurrent_semantics_reduce_identities
