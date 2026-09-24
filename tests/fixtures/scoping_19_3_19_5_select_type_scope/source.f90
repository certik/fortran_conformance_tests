! rule: S19.4-013
! covers: select-type-associate-name-separate-block-scope
program scoping_19_3_19_5_select_type_scope
  implicit none
  integer :: checks
  type :: base_t
    integer :: tag = -1
  end type
  type, extends(base_t) :: child_t
    integer :: payload = -2
  end type
  class(base_t), allocatable :: poly
  integer :: item, seen
  checks = 0
  item = 99
  seen = -3
  allocate(child_t :: poly)
  select type (item => poly)
  type is (child_t)
    item%tag = 505
    item%payload = 506
    seen = item%tag + item%payload
  class default
    seen = -5000
  end select
  if (seen /= 1011) then
    write(*,'(a)') 'SCOPE:select_type_scope:seen'
    error stop
  end if
  checks = checks + 1
  if (item /= 99) then
    write(*,'(a)') 'SCOPE:select_type_scope:outer'
    error stop
  end if
  checks = checks + 1
  if (checks /= 2) then
    write(*,'(a)') 'SCOPE:select_type_scope:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 SELECT TYPE SCOPE OK'
contains
end program scoping_19_3_19_5_select_type_scope
