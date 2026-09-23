! rule: S9.4.2-003
! covers: base-object-leftmost
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_base_object_leftmost
  implicit none
  type :: inner_t
    integer :: alpha
    integer :: beta
  end type inner_t
  type :: cell_t
    integer :: alpha
    integer :: beta
    integer :: avec(-5:-3)
    integer :: bvec(-5:-3)
    integer :: grid(-4:-2,5:8)
    integer :: other_grid(-4:-2,5:8)
    type(inner_t) :: inner
    type(inner_t) :: other_inner
  end type cell_t
  type(cell_t) :: obj, x(2:6)
  type(cell_t) :: left_obj, right_obj
  integer :: checks
  checks=0
  x(2)%alpha = 263
  x(3)%alpha = 313
  x(2)%beta = 317
  if (x(2)%alpha /= 263) then
    write(*,'(a)') 'SC:base_object_leftmost:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 317) then
    write(*,'(a)') 'SC:base_object_leftmost:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:base_object_leftmost:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  left_obj%inner%alpha = 971
  left_obj%inner%beta = 983
  right_obj%inner%alpha = 1091
  right_obj%inner%beta = 1103
  if (left_obj%inner%alpha /= 971) then
    write(*,'(a)') 'SC:base_object_leftmost:leftmost-base-object'
    error stop
  end if
  checks=checks+1
  if (right_obj%inner%alpha /= 1091) then
    write(*,'(a)') 'SC:base_object_leftmost:right-object-control'
    error stop
  end if
  checks=checks+1
  if (left_obj%inner%beta /= 983) then
    write(*,'(a)') 'SC:base_object_leftmost:nested-neighbor-control'
    error stop
  end if
  checks=checks+1
  if (right_obj%inner%beta /= 1103) then
    write(*,'(a)') 'SC:base_object_leftmost:right-nested-neighbor-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 7) then
    write(*,'(a)') 'SC:base_object_leftmost:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT BASE OBJECT LEFTMOST OK'
end program structure_component_base_object_leftmost
