! rule: S19.4-012
! covers: select-rank-associate-name-separate-block-scope
program scoping_19_3_19_5_select_rank_scope
  implicit none
  integer :: checks
  integer :: item, rank_array(2), seen
  checks = 0
  item = 99
  rank_array = -1
  seen = -2
  call rank_probe(rank_array, seen)
  if (rank_array(1) /= 404) then
    write(*,'(a)') 'SCOPE:select_rank_scope:array'
    error stop
  end if
  checks = checks + 1
  if (seen /= 3) then
    write(*,'(a)') 'SCOPE:select_rank_scope:seen'
    error stop
  end if
  checks = checks + 1
  if (item /= 99) then
    write(*,'(a)') 'SCOPE:select_rank_scope:outer'
    error stop
  end if
  checks = checks + 1
  if (checks /= 3) then
    write(*,'(a)') 'SCOPE:select_rank_scope:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 SELECT RANK SCOPE OK'
contains
  subroutine rank_probe(a, seen)
    integer, intent(inout) :: a(..)
    integer, intent(inout) :: seen
    select rank (item => a)
    rank (1)
      item(1) = 404
      seen = rank(item) + size(item)
    rank default
      seen = -404
    end select
  end subroutine
end program scoping_19_3_19_5_select_rank_scope
