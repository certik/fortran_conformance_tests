! rule: S19.4-009
! covers: default-typed-index-common-block-exception
! covers: default-typed-index-scalar-variable-exception
module scoping_index_common_holder
  implicit none
  integer :: common_payload
  common /idx/ common_payload
end module

program scoping_19_3_19_5_index_exceptions
  use scoping_index_common_holder, only: common_payload
  implicit integer (i)
  integer :: checks
  integer :: i, scalar_values(3), common_values(3)
  checks = 0
  i = 99
  common_payload = -909
  scalar_values = -1
  common_values = -2
  do concurrent (i = 1:3)
    scalar_values(i) = i
  end do
  do concurrent (idx = 1:3)
    common_values(idx) = idx + 10
  end do
  if (any(scalar_values /= [1, 2, 3])) then
    write(*,'(a)') 'SCOPE:index_exceptions:scalar-index-values'
    error stop
  end if
  checks = checks + 1
  if (i /= 99) then
    write(*,'(a)') 'SCOPE:index_exceptions:scalar-index-outer'
    error stop
  end if
  checks = checks + 1
  if (any(common_values /= [11, 12, 13])) then
    write(*,'(a)') 'SCOPE:index_exceptions:common-index-values'
    error stop
  end if
  checks = checks + 1
  if (common_payload /= -909) then
    write(*,'(a)') 'SCOPE:index_exceptions:common-index-storage'
    error stop
  end if
  checks = checks + 1
  if (checks /= 4) then
    write(*,'(a)') 'SCOPE:index_exceptions:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 INDEX EXCEPTIONS OK'
contains
end program scoping_19_3_19_5_index_exceptions
