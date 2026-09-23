! rule: S9.4.2-001
! covers: scalar-component
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_scalar_component
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
  x(2)%alpha = 229
  x(3)%alpha = 313
  x(2)%beta = 293
  if (x(2)%alpha /= 229) then
    write(*,'(a)') 'SC:scalar_component:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 293) then
    write(*,'(a)') 'SC:scalar_component:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:scalar_component:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%alpha = 523
  obj%beta = 641
  if (obj%alpha /= 523) then
    write(*,'(a)') 'SC:scalar_component:scalar-alpha'
    error stop
  end if
  checks=checks+1
  if (obj%beta /= 641) then
    write(*,'(a)') 'SC:scalar_component:scalar-beta-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 5) then
    write(*,'(a)') 'SC:scalar_component:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT SCALAR COMPONENT OK'
end program structure_component_scalar_component
