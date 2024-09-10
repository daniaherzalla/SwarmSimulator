# Swarm Simulator

This code is an expansion of Florimond Manca's work: https://github.com/florimondmanca/pyboids

## Class definition

- `Drone` : contains the position and velocity of a given drone and packs several methods implementing the previous rules:
	- `align(self, others)`
	- `cohere(self, others)`
	- `separate(self, others)`
- `Swarm` : groups a certain number of `Drone` objects and manages their interactions.
- `Simulation` : runs the simulation (Pygame application), with interactive functionalities.

## How it all works

This is a simulation that aims at representing or recreating the behaviour of flocking birds. There are three rules that the drones simulation relies on:

- alignment : the velocities of nearby drones tend to align (make a drone's velocity align with the average velocity of nearby drones)
- cohesion : drones cluster together (average the position of nearby drones and move a bit towards that position;)
- separation : drones tend to repel when they are too near from one another (if a drone enters a critical radius, move away from it with a velocity directed in the opposite direction.)

Each of these rules is associated with a contribution to the velocity at the next simulation frame.

### Rules in equation

**Notations.** Given a set of $N$ drones and a time of simulation $t^n$ :

- let $v^n_i$ and $p^n_i$ respectively be the velocity and position of a drone of interest $i$ ;
- let $v^n_i$ and $p^n_j$ respectively be the velocity and position of any other drone $j$, $j \neq i$ ;
- let $m_i$ be the number of drones in the neighborhood of current drone $i$, the latter being excluded.

#### Alignment

Alignment translates to a contribution $v_a$ to the next velocity $v^{n+1}_i$ given be the center of mass of neighbors' velocities:

$$ v_a = K_a ((\frac{1}{m_i}\sum_{j=1}^{m_i} v^n_j) - v^n_i) $$

where $K_a$ is typically around 0.1 or 0.15.

#### Cohesion

Cohesion means that drones tend to fly together (that is, to fly towards the center of mass of their neighbors' positions), hence a contribution $v_c$ to the next velocity $v^{n+1}_i$ given by:

$$ v_c = K_c ((\frac{1}{m_i} \sum_{j=1}^{m_i} p^n_j) - p^n_i)$$

where $K_c$ is typically around 0.01.

#### Separation

Separation refers to the fact that near drones tend to repel one another, as they don't like that much to be too close. This yields to a contribution $v_s$ given by:

$$ v_s = - \sum_{j,\ dist(i, j)\ \leq\ R_s} (p_j^n - v^n_i) $$

where $R_s$ is the critical radius of separation. Only drones $j$ closer than $R_s$ contribute to the separation effect. The overall "density" of the flocking will then be given by this parameter.

#### Bounding the velocity

In reality, birds can't go arbitrarily fast. We can add another rule to limit the velocity of drones with a $v_{lim}$ parameter. Typical value could be 20.

#### Bounding the position

For simulation purposes, drones will need to remain in a given box (the screen). We will simply say that if the position in $x$ or $y$ direction exceeds a certain amount, then add a velocity $v_b$ in the opposite direction to induce a smooth return to the simulation space. Typical value of $v_b$ is around 10.
Alternatively, they can wrap around the screen.

## Parameters definition

All parameters of the simulation will be grouped in a `params.py` file.

## Resources

http://www.vergenet.net/~conrad/drones/pseudocode.html

http://gamedevelopment.tutsplus.com/series/understanding-steering-behaviors--gamedev-12732