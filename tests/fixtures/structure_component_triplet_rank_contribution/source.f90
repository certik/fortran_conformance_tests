! rule: S9.4.2-002
! covers: triplet-rank-contribution
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_triplet_rank_contribution
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
  x(2)%alpha = 241
  x(3)%alpha = 313
  x(2)%beta = 301
  if (x(2)%alpha /= 241) then
    write(*,'(a)') 'SC:triplet_rank_contribution:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 301) then
    write(*,'(a)') 'SC:triplet_rank_contribution:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:triplet_rank_contribution:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%grid(-4,7) = 473
  obj%grid(-3,7) = 373
  obj%grid(-2,7) = 273
  obj%other_grid(-4,7) = 673
  obj%other_grid(-3,7) = 573
  if (any(shape(obj%grid(-4:-3,7)) /= [2])) then
    write(*,'(a)') 'SC:triplet_rank_contribution:shape'
    error stop
  end if
  checks=checks+1
  if (any(lbound(obj%grid(-4:-3,7)) /= [1])) then
    write(*,'(a)') 'SC:triplet_rank_contribution:lbound'
    error stop
  end if
  checks=checks+1
  if (any(ubound(obj%grid(-4:-3,7)) /= [2])) then
    write(*,'(a)') 'SC:triplet_rank_contribution:ubound'
    error stop
  end if
  checks=checks+1
  if (any(obj%grid(-4:-3,7) /= [473, 373])) then
    write(*,'(a)') 'SC:triplet_rank_contribution:values'
    error stop
  end if
  checks=checks+1
  if (obj%grid(-2,7) /= 273) then
    write(*,'(a)') 'SC:triplet_rank_contribution:triplet-shift-value-control'
    error stop
  end if
  checks=checks+1
  if (obj%other_grid(-4,7) /= 673) then
    write(*,'(a)') 'SC:triplet_rank_contribution:other-grid-first-control'
    error stop
  end if
  checks=checks+1
  if (obj%other_grid(-3,7) /= 573) then
    write(*,'(a)') 'SC:triplet_rank_contribution:other-grid-second-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 10) then
    write(*,'(a)') 'SC:triplet_rank_contribution:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT TRIPLET RANK CONTRIBUTION OK'
end program structure_component_triplet_rank_contribution
