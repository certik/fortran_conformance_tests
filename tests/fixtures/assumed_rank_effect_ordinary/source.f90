program assumed_rank_ordinary_effect
  implicit none
  integer :: scalar, vector(3), matrix(2,3)
  integer :: visits, returns, observer_checks, main_checks
  integer :: scalar_visits, rank_one_visits, rank_two_visits
  scalar=11
  vector=12
  matrix=13
  visits=0
  returns=0
  observer_checks=0
  main_checks=0
  scalar_visits=0
  rank_one_visits=0
  rank_two_visits=0
  call observe(scalar, 0, 1)
  returns=returns+1
  call observe(vector, 1, 2)
  returns=returns+1
  call observe(matrix, 2, 3)
  returns=returns+1
  if (visits /= 3) then
    write(*,'(a)') 'ARE:ordinary:total-visits'
    error stop
  end if
  main_checks=main_checks+1
  if (scalar_visits /= 1) then
    write(*,'(a)') 'ARE:ordinary:category-0'
    error stop
  end if
  main_checks=main_checks+1
  if (rank_one_visits /= 1) then
    write(*,'(a)') 'ARE:ordinary:category-1'
    error stop
  end if
  main_checks=main_checks+1
  if (rank_two_visits /= 1) then
    write(*,'(a)') 'ARE:ordinary:category-2'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 3) then
    write(*,'(a)') 'ARE:ordinary:normal-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (observer_checks /= 6) then
    write(*,'(a)') 'ARE:ordinary:observer-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 6) then
    write(*,'(a)') 'ARE:ordinary:caller-checks'
    error stop
  end if
  write(*,'(a)') 'ASSUMED RANK ORDINARY OK'
contains
  subroutine observe(x, expected_rank, expected_visit)
    implicit none
    integer, intent(in) :: x(..)
    integer, intent(in) :: expected_rank, expected_visit
    integer :: observed_rank
    visits=visits+1
    observed_rank=rank(x)
    if (observed_rank /= expected_rank) then
      write(*,'(a,i1)') 'ARE:ordinary:observer-rank:activation=', visits
      error stop
    end if
    observer_checks=observer_checks+1
    if (visits /= expected_visit) then
      write(*,'(a,i1)') 'ARE:ordinary:observer-visit:activation=', visits
      error stop
    end if
    observer_checks=observer_checks+1
    select case (observed_rank)
    case (0)
      scalar_visits=scalar_visits+1
    case (1)
      rank_one_visits=rank_one_visits+1
    case (2)
      rank_two_visits=rank_two_visits+1
    end select
  end subroutine observe
end program assumed_rank_ordinary_effect
