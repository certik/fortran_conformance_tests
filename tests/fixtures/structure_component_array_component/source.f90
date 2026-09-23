! rule: S9.4.2-001
! covers: array-component
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_array_component
  implicit none
  type :: cell_t
    integer :: alpha
    integer :: beta
    integer :: avec(-5:-3)
    integer :: bvec(-5:-3)
    integer :: grid(-4:-2,5:8)
    integer :: other_grid(-4:-2,5:8)
  end type cell_t
  type(cell_t) :: obj, x(2:6)
  integer :: checks
  checks=0
  x(2)%alpha = 233
  x(3)%alpha = 313
  x(2)%beta = 295
  if (x(2)%alpha /= 233) then
    write(*,'(a)') 'SC:array_component:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 295) then
    write(*,'(a)') 'SC:array_component:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:array_component:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%avec = [719, 727, 733]
  obj%bvec = [839, 853, 857]
  if (any(shape(obj%avec) /= [3])) then
    write(*,'(a)') 'SC:array_component:shape'
    error stop
  end if
  checks=checks+1
  if (any(lbound(obj%avec) /= [-5])) then
    write(*,'(a)') 'SC:array_component:lbound'
    error stop
  end if
  checks=checks+1
  if (any(ubound(obj%avec) /= [-3])) then
    write(*,'(a)') 'SC:array_component:ubound'
    error stop
  end if
  checks=checks+1
  if (any(obj%avec /= [719, 727, 733])) then
    write(*,'(a)') 'SC:array_component:values'
    error stop
  end if
  checks=checks+1
  if (any(obj%bvec /= [839, 853, 857])) then
    write(*,'(a)') 'SC:array_component:neighbor-vector-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 8) then
    write(*,'(a)') 'SC:array_component:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT ARRAY COMPONENT OK'
end program structure_component_array_component
